from app.graph.state import ScamState


# Assuming you have a rule checking utility or function.
# Let's write a robust wrapper that evaluates the message against your rules.

def run_rules_check(state: ScamState) -> ScamState:
    message = state["message"]

    # Example rule evaluation logic (customize based on your checks.py)
    flags = []
    score = 0

    # Basic keyword / regex checks
    msg_lower = message.lower()

    if any(word in msg_lower for word in ["bvn", "otp", "suspended", "blocked", "pin"]):
        flags.append({"id": "sensitive_info", "label": "Requests Sensitive Information (BVN/OTP/PIN)", "weight": 40})
        score += 40

    if any(word in msg_lower for word in ["http://", "https://", "bit.ly", "t.co"]):
        flags.append({"id": "phishing_link", "label": "Contains URL / Link", "weight": 30})
        score += 30

    if any(word in msg_lower for word in ["urgent", "immediately", "24 hours", "suspended"]):
        flags.append({"id": "urgency", "label": "High Urgency / Coercion", "weight": 20})
        score += 20

    score = min(score, 100)

    # Determine initial rule verdict
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