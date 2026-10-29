import re
from typing import Dict, Any, List

# High-risk trigger keywords requiring strict word boundary checking
SENSITIVE_KEYWORDS = [r'\botp\b', r'\bpin\b', r'\bbvn\b', r'\bpassword\b', r'\bpw\b']
FINANCIAL_KEYWORDS = [r'\bloan\b', r'\btransfer\b', r'\bdebit\b', r'\bcredit\b', r'\baccount\b']

# Regex patterns for malicious indicators
LOOKALIKE_DOMAIN_PATTERN = re.compile(
    r'https?://[^\s]*(?:gtb-|access-|zenith-|opay-|palmpay-|verify-|secure-|update-|login-|kyc-|airtel-|mtn-|glo-)[^\s]*',
    re.IGNORECASE
)
SHORTLINK_PATTERN = re.compile(
    r'https?://(?:bit\.ly|t\.co|goo\.gl|tinyurl\.com|ow\.ly|is\.gd|buff\.ly|shorturl\.at)/[^\s]+',
    re.IGNORECASE
)
URGENCY_PATTERN = re.compile(
    r'\b(within 24 hours|immediate(?:ly)?|urgent(?:ly)?|final warning|today only|expires in|deactivated today|suspended|'
    r'sharp sharp|now now|quick quick|'
    r'kia-kia|kiakia|pajawiri|laarin wakati|wakati 24|'
    r'gaggawa|nan da nan|cikin sa\'o\'i|sa\'o\'i 24|'
    r'ozugbo|ngwa ngwa|tupu awa|awa 24)\b',
    re.IGNORECASE
)

# Explicit phrase patterns for credential harvesting vs disclaimers (English, Pidgin, Yoruba, Hausa, Igbo)
CREDENTIAL_DEMAND_PATTERN = re.compile(
    r'\b(send|verify|confirm|enter|update|provide|share|claim|te|tura|tinye|nyefee)\b.*'
    r'\b(otp|pin|bvn|password|card details|lambar sirri|koodu)\b',
    re.IGNORECASE
)
DISCLAIMER_PATTERN = re.compile(
    r'\b(never|do not|don\'t|will not|no share|ma se so|ma fi han|kada ka bayyana|kada ka ba kowa|ekekwala|ekwula)\b.*'
    r'\b(share|give|disclose|send|bayyana|kowa|tinye|nyefee)\b',
    re.IGNORECASE
)

def scan_rules(message: str) -> Dict[str, Any]:
    text = message.lower()
    flags: List[Dict[str, Any]] = []
    score = 0
    floor_reasons = []

    # 1. Lookalike / Phishing domain (High risk -> immediate hard floor)
    if LOOKALIKE_DOMAIN_PATTERN.search(message):
        flags.append({"id": "lookalike_domain", "label": "Lookalike / Phishing Domain Detected", "weight": 50})
        score += 50
        floor_reasons.append("Contains lookalike or suspicious banking domain")

    # 2. Shortened URLs (Moderate weight, 15 pts)
    if SHORTLINK_PATTERN.search(message):
        flags.append({"id": "shortlink", "label": "Shortened URL Used", "weight": 15})
        score += 15

    # 3. Urgency & threat pressure (Moderate weight, 20 pts)
    if URGENCY_PATTERN.search(message):
        flags.append({"id": "urgency_trigger", "label": "High Urgency / Pressure Language", "weight": 20})
        score += 20

    # 4. Credential theft demand vs legitimate safety disclaimer
    if CREDENTIAL_DEMAND_PATTERN.search(message):
        # Ignore if it's a security warning ("Never share your OTP")
        if not DISCLAIMER_PATTERN.search(message):
            flags.append({"id": "sensitive_data_request", "label": "Sensitive Credential Request (OTP/PIN/BVN)", "weight": 35})
            score += 35
            floor_reasons.append("Demands sensitive credentials (OTP/PIN/BVN)")

    # 5. Financial threats / account restriction notices
    has_financial_term = any(re.search(kw, text) for kw in FINANCIAL_KEYWORDS)
    if has_financial_term and not any(f["id"] == "lookalike_domain" for f in flags):
        if re.search(r'\b(overdue|suspended|deactivated|block|arrest|court|police)\b', text):
            flags.append({"id": "financial_threat", "label": "Financial Threat / Restriction Notice", "weight": 25})
            score += 25

    # Cap score at 100
    score = min(score, 100)

    # Hard floor rule: Require score >= 50 or confirmed lookalike domain/credential theft
    hard_floor = score >= 50 or any(f["id"] in ["lookalike_domain", "sensitive_data_request"] for f in flags)

    return {
        "score": score,
        "flags": flags,
        "hard_floor": hard_floor,
        "floor_reasons": floor_reasons
    }