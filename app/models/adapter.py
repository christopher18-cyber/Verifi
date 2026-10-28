import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import ValidationError

from .schemas import Analysis

load_dotenv()

PROMPT = (Path(__file__).parent.parent / "prompts" / "analyst.txt").read_text(encoding="utf-8")
_client = None


def model_enabled() -> bool:
    return os.getenv("MODEL_ENABLED", "true").lower() == "true"


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=os.environ["MODEL_BASE_URL"],
            api_key=os.environ["MODEL_API_KEY"],
            timeout=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
        )
    return _client


def _extract_json(text: str) -> dict:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start : end + 1])


async def analyse(message: str, evidence: dict) -> Analysis | None:
    """Returns a validated Analysis, or None if the model is off or fails."""
    if not model_enabled():
        return None

    user = f"Message:\n{message}\n\nRule evidence:\n{json.dumps(evidence, ensure_ascii=False)}"
    messages = [{"role": "system", "content": PROMPT}, {"role": "user", "content": user}]
    text = ""

    for _ in range(2):  # one try plus one retry with the error fed back
        try:
            resp = await _get_client().chat.completions.create(
                model=os.environ["MODEL_NAME"],
                messages=messages,
                temperature=0,
                max_tokens=1000,
            )
            text = resp.choices[0].message.content or ""
            result = Analysis(**_extract_json(text))
            result.quotes = [q for q in result.quotes if q in message]  # drop invented quotes
            return result
        except ValueError as err:  # bad JSON or failed schema check
            messages += [
                {"role": "assistant", "content": text},
                {"role": "user", "content": f"Your reply was invalid ({err}). Reply again with valid JSON only."},
            ]
        except Exception:  # timeout, rate limit, network: let the caller fall back to rules
            return None
    return None