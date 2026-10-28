import argparse
import asyncio
import csv
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

from app.graph.build import graph          # noqa: E402
from app.models.adapter import analyse     # noqa: E402

HERE = Path(__file__).parent


def load(path, split):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("message", "").strip()]
    if split:
        rows = [r for r in rows if r.get("split", "").strip().lower() == split]
    return rows


async def run_graph(msg, model_on):
    os.environ["MODEL_ENABLED"] = "true" if model_on else "false"
    start = time.time()
    final = (await graph.ainvoke({"message": msg, "language": "en"}))["final"]
    secs = time.time() - start
    if model_on and final["degraded"]:       # model failed: not a real hybrid result
        return None, None, secs
    return final["verdict"], final["category"], secs


async def run_model_only(msg):
    os.environ["MODEL_ENABLED"] = "true"
    start = time.time()
    a = await analyse(" ".join(msg.split())[:2000], {})
    secs = time.time() - start
    return (a.verdict, a.category, secs) if a else (None, None, secs)


def pct(a, b):
    return f"{100 * a / b:.0f}% ({a}/{b})" if b else "n/a"


def summarise(name, recs):
    ok = [r for r in recs if r["pred"]]
    scams = [r for r in ok if r["label"] == "scam"]
    genuine = [r for r in ok if r["label"] == "genuine"]
    pidgin = [r for r in ok if r["pidgin"]]
    avg = sum(r["secs"] for r in recs) / len(recs) if recs else 0
    return (f"| {name} | {pct(sum(r['pred'] == r['label'] for r in ok), len(ok))} "
            f"| {pct(sum(r['pred'] == 'genuine' for r in scams), len(scams))} "
            f"| {pct(sum(r['pred'] != 'genuine' for r in genuine), len(genuine))} "
            f"| {pct(sum(r['pred'] == r['label'] for r in pidgin), len(pidgin))} "
            f"| {avg:.1f}s | {len(recs) - len(ok)} |")


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", default=str(HERE / "dataset.csv"))
    p.add_argument("--split", default="", help="dev or test (default: all rows)")
    p.add_argument("--delay", type=float, default=2.5, help="seconds between model calls")
    p.add_argument("--skip-model-only", action="store_true")
    args = p.parse_args()

    rows = load(args.data, args.split.lower())
    print(f"Evaluating {len(rows)} messages" + (f" (split: {args.split})" if args.split else ""))

    setups = ["Rules only", "Hybrid"] + ([] if args.skip_model_only else ["Model only"])
    results = {s: [] for s in setups}

    for i, row in enumerate(rows, 1):
        msg = row["message"]
        print(f"  {i}/{len(rows)}", end="\r")
        calls = {
            "Rules only": lambda: run_graph(msg, False),
            "Hybrid": lambda: run_graph(msg, True),
            "Model only": lambda: run_model_only(msg),
        }
        for s in setups:
            pred, cat, secs = await calls[s]()
            results[s].append({
                "id": row.get("id", i), "label": row["label"].strip().lower(),
                "category": row.get("category", "").strip(),
                "pidgin": row.get("language", "").strip().lower().startswith("p"),
                "pred": pred, "pred_category": cat, "secs": secs, "message": msg,
            })
            if s != "Rules only":
                await asyncio.sleep(args.delay)

    table = [
        "| Setup | Verdict accuracy | Scams missed | Genuine flagged | Pidgin accuracy | Avg time | Failed calls |",
        "|---|---|---|---|---|---|---|",
        *[summarise(s, results[s]) for s in setups],
    ]
    out = "\n".join(table)
    print("\n\n" + out)
    (HERE / "results.md").write_text(out + "\n", encoding="utf-8")

    with open(HERE / "predictions.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "setup", "label", "pred", "category", "pred_category", "secs"])
        for s in setups:
            for r in results[s]:
                w.writerow([r["id"], s, r["label"], r["pred"] or "FAILED", r["category"],
                            r["pred_category"] or "", f"{r['secs']:.2f}"])

    print("\nWrong or failed (use these for your README failure list):")
    for s in setups:
        for r in results[s]:
            if r["pred"] != r["label"]:
                print(f"  [{s}] id={r['id']} label={r['label']} got={r['pred'] or 'FAILED'}: {r['message'][:70]}")


if __name__ == "__main__":
    asyncio.run(main())