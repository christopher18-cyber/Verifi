import os
import json
from openai import AsyncOpenAI
from app.graph.state import ScamState


LANGUAGE_CONFIGS = {
    "en": {
        "name": "English",
        "instruction": "Write the 'reason' field strictly in clear, professional English.",
        "fallback_reason": lambda score: f"Evaluated via rules (score {score}/100). LLM disabled.",
        "error_reason": lambda score, err: f"Rule score {score}/100 (LLM error: {err})",
    },
    "pidgin": {
        "name": "Nigerian Pidgin",
        "instruction": "Write the 'reason' field strictly in natural, authentic Nigerian Pidgin English (e.g. 'Dis message na real scam oo, bank staff no dey ever ask for your OTP or BVN').",
        "fallback_reason": lambda score: f"Evaluated via rule score {score}/100. LLM dey off.",
        "error_reason": lambda score, err: f"Rule score {score}/100 (LLM get error: {err})",
    },
    "yoruba": {
        "name": "Yorùbá",
        "instruction": "Write the 'reason' field strictly in authentic, fluent Yorùbá language (e.g. 'Ifiranṣẹ yii jẹ ẹtan ti o lewu (scam). Ile-ifowopamọ kii yoo beere fun nọmba BVN tabi OTP rẹ rara').",
        "fallback_reason": lambda score: f"A ṣe ayẹwo pẹlu awọn ofin (aami {score}/100). Eto AI wa ni pipa.",
        "error_reason": lambda score, err: f"Aami ofin {score}/100 (Aṣiṣe AI: {err})",
    },
    "hausa": {
        "name": "Hausa",
        "instruction": "Write the 'reason' field strictly in authentic, fluent Hausa language (e.g. 'Wannan sakon na zamba ne (scam). Banki ba zai taba tambayar lambobin BVN ko na sirri (OTP) ba').",
        "fallback_reason": lambda score: f"An kimanta ta hanyar dokoki (maki {score}/100). AI yana a kashe.",
        "error_reason": lambda score, err: f"Makin doka {score}/100 (Kuskuren AI: {err})",
    },
    "igbo": {
        "name": "Igbo",
        "instruction": "Write the 'reason' field strictly in authentic, fluent Igbo language (e.g. 'Ozi a bụ aghụghọ zuru oke (scam). Ụlọ akụ agaghị ajụ gị maka nọmba BVN ma ọ bụ koodu nzuzo OTP gị').",
        "fallback_reason": lambda score: f"A nyochara ya site na iwu nchekwa (akara {score}/100). AI adịghị arụ ọrụ.",
        "error_reason": lambda score, err: f"Akara iwu {score}/100 (Njehie AI: {err})",
    },
}


async def run_llm_evaluation(state: ScamState) -> ScamState:
    message = state["message"]
    raw_lang = state.get("language", "en")
    lang_key = raw_lang.lower().strip() if raw_lang else "en"
    config = LANGUAGE_CONFIGS.get(lang_key, LANGUAGE_CONFIGS["en"])
    rules_data = state["rules"]

    api_key = os.getenv("MODEL_API_KEY")
    base_url = os.getenv("MODEL_BASE_URL", "https://api.groq.com/openai/v1")
    model_name = os.getenv("MODEL_NAME", "openai/gpt-oss-20b")

    if not api_key or os.getenv("MODEL_ENABLED", "true").lower() == "false":
        verdict = "scam" if rules_data["score"] >= 50 else "genuine"
        state["final"] = {
            "verdict": verdict,
            "category": "rule_fallback",
            "reason": config["fallback_reason"](rules_data["score"]),
            "rules": rules_data,
            "language": lang_key
        }
        return state

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        prompt = f"""You are an expert cybersecurity fraud detection analyst specializing in Nigerian mobile communications (SMS, WhatsApp, email).
You are evaluating messages that may be written in English, Nigerian Pidgin, Yorùbá, Hausa, or Igbo.

Target Output Language: {config['name'].upper()}
Language Instruction: {config['instruction']}

Deterministic rule engine score: {rules_data['score']}/100.
Triggered rules: {json.dumps(rules_data['flags'])}
Message to evaluate: "{message}"

Evaluate the message for:
1. Impersonation of Nigerian banks (GTBank, Access Bank, Zenith, UBA, First Bank, etc.) or fintechs (OPay, PalmPay, Moniepoint, Kuda).
2. Urgency coercion or panic-inducing threats (threat of account suspension, BVN invalidation, police/court threats).
3. Sensitive credential harvesting (demanding BVN, OTP, PIN, password, card details).
4. Phishing links, shortened URLs, or lookalike domains (.xyz, .top, fake subdomains).
5. Unrealistic loan approvals or lottery/prize claims.

Return a JSON response with this exact structure:
{{
    "verdict": "scam" or "genuine",
    "category": "bank_phishing", "loan_scam", "prize_and_fee", "fake_job", "impersonation", or "legitimate_alert",
    "reason": "Clear explanation adhering strictly to {config['name']}."
}}
"""

        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a fraud detection assistant that outputs strict JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )

        llm_result = json.loads(response.choices[0].message.content)

        state["llm_output"] = llm_result
        state["final"] = {
            "verdict": llm_result.get("verdict", "scam" if rules_data["score"] >= 50 else "genuine"),
            "category": llm_result.get("category", "bank_phishing"),
            "reason": llm_result.get("reason", f"Evaluated with rule score {rules_data['score']}/100."),
            "rules": rules_data,
            "language": lang_key
        }

    except Exception as e:
        verdict = "scam" if rules_data["score"] >= 50 else "genuine"
        state["final"] = {
            "verdict": verdict,
            "category": "fallback",
            "reason": config["error_reason"](rules_data["score"], str(e)),
            "rules": rules_data,
            "language": lang_key
        }

    return state