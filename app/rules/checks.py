import re
from urllib.parse import urlparse

# Real sites. Verify and extend this list yourselves; I can't confirm every domain.
OFFICIAL_DOMAINS = {
    "gtbank.com", "zenithbank.com", "firstbanknigeria.com", "accessbankplc.com",
    "ubagroup.com", "fcmb.com", "sterling.ng", "wemabank.com", "kuda.com",
    "moniepoint.com", "opay-nigeria.com", "palmpay.com", "mtnonline.com",
    "mtn.ng", "ng.airtel.com", "cbn.gov.ng", "nibss-plc.com.ng",
}
SHORTENERS = {"bit.ly", "tinyurl.com", "cutt.ly", "t.co", "rb.gy", "is.gd",
              "shorturl.at", "tiny.cc", "ow.ly"}
BRAND_TOKENS = {"gtb", "gtbank", "gtco", "zenith", "firstbank", "accessbank", "uba",
                "fcmb", "sterling", "wema", "kuda", "opay", "palmpay", "moniepoint",
                "mtn", "airtel", "glo", "9mobile", "cbn", "nibss", "bvn", "nin"}
RISKY_TOKENS = {"secure", "verify", "login", "update", "claim", "reward", "alert", "support"}

URL_RE = re.compile(
    r"(https?://[^\s]+|\b(?:[a-z0-9-]+\.)+(?:com|ng|xyz|top|ly|info|link|co|net|org|"
    r"click|site|online|live|icu|cc)\b(?:/[^\s]*)?)", re.I)

SECRET_WORD = re.compile(
    r"\b(otp|pin|bvn|nin|password|passcode|cvv|card (?:number|details)|token)\b", re.I)
ASK_VERB = re.compile(
    r"\b(send|share|provide|give|confirm|verify|reply|enter|submit|update|forward|tell)\b", re.I)
NEGATION = re.compile(r"\b(never|do not|don'?t|dont|no one|nobody)\b", re.I)

# (id, label, weight, pattern)
PATTERNS = [
    ("urgency", "Pressure or deadline", 15, re.compile(
        r"\b(within \d+\s?(?:hours?|hrs?|minutes?|mins?|days?)|immediately|urgent(?:ly)?|asap|"
        r"right now|expires? (?:today|soon)|last warning|final notice|today only|act now|"
        r"before midnight)\b", re.I)),
    ("account_threat", "Threat to block or close your account", 20, re.compile(
        r"\b(account (?:has been |is |will be |don )?(?:suspended|blocked|block|locked|frozen|"
        r"closed|deactivated|restricted)|will be (?:blocked|suspended|closed|deactivated)|"
        r"permanent(?:ly)? (?:block|suspen)\w*)\b", re.I)),
    ("prize", "Prize or reward you never entered for", 20, re.compile(
        r"\b(congratulations|you (?:have )?won|you['’]ve won|winner|claim your "
        r"(?:prize|reward|gift)|mega promo|lucky (?:winner|draw)|jackpot)\b", re.I)),
    ("advance_fee", "Asks for a fee first", 25, re.compile(
        r"\b(?:(?:processing|registration|clearance|activation|delivery|admin|verification|"
        r"release|insurance|application) fee|(?:send|pay|transfer)\s+(?:a\s+)?(?:₦|n|ngn)?\s?"
        r"\d[\d,\.]*\s?k?\b.{0,40}\b(?:to|before)\s+(?:claim|start|activate|receive|get|"
        r"release|unlock|begin))\b", re.I)),
    ("airtime_request", "Asks you to send airtime or credit", 20, re.compile(
        r"\b(?:send|buy|load|recharge)\b.{0,25}\b(?:airtime|data|credit)\b", re.I)),
    ("contact_threat", "Threatens to shame you through your contacts", 30, re.compile(
        r"\b(contact list|your contacts|everyone in your (?:phone|contacts?)|"
        r"send your (?:photo|picture|pictures)|expose you|shame you|"
        r"we will (?:call|text|message|send) (?:your|everyone|all))\b", re.I)),
    ("too_good_income", "Unrealistic earnings promise", 10, re.compile(
        r"\b(?:earn|make)\s+(?:₦|n|ngn)?\s?\d[\d,]*k?\s+(?:daily|weekly|monthly|"
        r"per (?:day|week))\b", re.I)),
    ("investment_hype", "Guaranteed or doubled returns", 15, re.compile(
        r"\b(double your (?:money|investment)|guaranteed (?:returns?|profit)|"
        r"\d+\s?% (?:daily|weekly|returns?)|investment (?:plan|opportunity))\b", re.I)),
]
LINK_WEIGHTS = {"lookalike": 35, "shortener": 20, "unknown": 10}
LINK_LABELS = {
    "lookalike": "Link imitates a bank or network but is not its real site",
    "shortener": "Shortened link hides the real destination",
    "unknown": "Link to a site we do not recognise",
}


def _kind(host: str) -> str:
    if any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS):
        return "official"
    if host in SHORTENERS:
        return "shortener"
    tokens = set(re.split(r"[.\-]", host))
    if tokens & BRAND_TOKENS or tokens & RISKY_TOKENS:
        return "lookalike"
    return "unknown"


def extract_links(text: str) -> list[dict]:
    links, seen = [], set()
    for m in URL_RE.finditer(text):
        if m.start() > 0 and text[m.start() - 1] == "@":  # email address, not a link
            continue
        raw = m.group(0).rstrip(".,;:!?)\"'")
        host = (urlparse(raw if "://" in raw else "http://" + raw).hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        if host and host not in seen:
            seen.add(host)
            links.append({"url": raw, "host": host, "kind": _kind(host)})
    return links


def _secret_requests(text: str) -> tuple[list[str], list[str]]:
    asks, warnings = [], []
    for sentence in re.split(r"(?<=[.!?])\s+|\n", text):
        if SECRET_WORD.search(sentence) and ASK_VERB.search(sentence):
            (warnings if NEGATION.search(sentence) else asks).append(sentence.strip())
    return asks, warnings


def scan_rules(message: str) -> dict:
    """Pure rule scan. Returns evidence for the model and a safety floor."""
    text = " ".join(message.split())
    flags, floor_reasons = [], []

    asks, warnings = _secret_requests(text)
    if asks:
        flags.append({"id": "secret_request", "label": "Asks for an OTP, PIN, BVN or password",
                      "weight": 40, "matches": asks})
        floor_reasons.append("asks for an OTP, PIN, BVN or password")
    elif warnings:
        flags.append({"id": "protective_warning", "label": "Warns you not to share secrets",
                      "weight": -25, "matches": warnings})

    for fid, label, weight, pattern in PATTERNS:
        found = [m.group(0) for m in pattern.finditer(text)]
        if found:
            flags.append({"id": fid, "label": label, "weight": weight, "matches": found})

    links = extract_links(text)
    for kind, weight in LINK_WEIGHTS.items():
        urls = [l["url"] for l in links if l["kind"] == kind]
        if urls:
            flags.append({"id": f"{kind}_link", "label": LINK_LABELS[kind],
                          "weight": weight, "matches": urls})
    if any(l["kind"] == "lookalike" for l in links):
        floor_reasons.append("contains a link that imitates a bank or network")

    score = max(0, min(100, sum(f["weight"] for f in flags)))
    return {
        "links": links,
        "flags": flags,
        "score": score,
        "hard_floor": bool(floor_reasons),
        "floor_reasons": floor_reasons,
        "protective_warning": any(f["id"] == "protective_warning" for f in flags),
    }