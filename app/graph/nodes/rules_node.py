from app.graph.state import ScamState

def run_rules_check(state: ScamState) -> ScamState:
    message = state["message"]
    flags = []
    score = 0
    msg_lower = message.lower()

    # Check for negative/advisory contexts first
    is_advisory = any(phrase in msg_lower for phrase in ["never share", "do not share", "don't share", "do not disclose"])

    # Only flag sensitive info requests if it's NOT an advisory message
    if not is_advisory and any(word in msg_lower for word in ["bvn", "otp", "suspended", "blocked", "pin"]):
        flags.append({"id": "sensitive_info", "label": "Requests Sensitive Information (OTP/PIN/BVN)", "weight": 40})
        score += 40

    if any(word in msg_lower for word in ["http://", "https://", "bit.ly", "t.co"]):
        flags.append({"id": "phishing_link", "label": "Contains External Link", "weight": 30})
        score += 30

    if any(word in msg_lower for word in ["urgent", "immediately", "24 hours"]):
        flags.append({"id": "urgency", "label": "High Urgency / Coercion", "weight": 20})
        score += 20

    score = min(score, 100)

    verdict = "genuine"
    if score >= 50:
        verdict = "scam"
    elif score >= 20:
        verdict = "suspicious"

    state["rules"] = {
        "score": score,
        "flags": flags,
        "verdict": verdict
    }
    return state