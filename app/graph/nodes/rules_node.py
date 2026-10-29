from app.graph.state import ScamState

def run_rules_check(state: ScamState) -> ScamState:
    message = state["message"]
    flags = []
    score = 0
    msg_lower = message.lower()

    # Check for negative/advisory contexts first (English, Pidgin, Yoruba, Hausa, Igbo)
    advisory_phrases = [
        "never share", "do not share", "don't share", "do not disclose",
        "no share", "no give anybody",
        "ma se so", "ma fi han", "ma so fun",
        "kada ka bayyana", "kada ka ba kowa", "kada ka tura",
        "ekekwala", "ekwula", "etinyeghi", "enyeghị onye ọ bụla"
    ]
    is_advisory = any(phrase in msg_lower for phrase in advisory_phrases)

    # 1. Sensitive information & Account threats
    sensitive_words = [
        "bvn", "otp", "pin", "password", "suspended", "blocked", "deactivated",
        "ti ti pa", "ti pa", "akanti",
        "dakatar", "rufe", "asusunka", "asusu", "lambar sirri",
        "mechiri", "emechiwo", "akauntu", "koodu"
    ]
    if not is_advisory and any(word in msg_lower for word in sensitive_words):
        flags.append({"id": "sensitive_info", "label": "Requests Sensitive Information (OTP/PIN/BVN/Threat)", "weight": 40})
        score += 40

    # 2. Phishing links & suspicious domains
    if any(word in msg_lower for word in ["http://", "https://", "bit.ly", "t.co", ".xyz", ".top", ".live"]):
        flags.append({"id": "phishing_link", "label": "Contains External / Phishing Link", "weight": 30})
        score += 30

    # 3. Urgency & Coercion (English, Pidgin, Yoruba, Hausa, Igbo)
    urgency_words = [
        "urgent", "immediately", "24 hours", "final warning", "today only",
        "sharp sharp", "now now", "quick quick",
        "kia-kia", "kiakia", "pajawiri", "laarin wakati", "wakati 24",
        "gaggawa", "nan da nan", "cikin sa'o'i", "sa'o'i 24",
        "ozugbo", "ngwa ngwa", "tupu awa", "awa 24"
    ]
    if any(word in msg_lower for word in urgency_words):
        flags.append({"id": "urgency", "label": "High Urgency / Coercion Language", "weight": 20})
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