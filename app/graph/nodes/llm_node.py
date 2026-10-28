import os
import json
from openai import AsyncOpenAI
from app.graph.state import ScamState


async def run_llm_evaluation(state: ScamState) -> ScamState:
    message = state["message"]
    language = state.get("language", "en")
    rules_data = state["rules"]

    api_key = os.getenv("MODEL_API_KEY")
    base_url = os.getenv("MODEL_BASE_URL", "https://api.groq.com/openai/v1")
    model_name = os.getenv("MODEL_NAME", "openai/gpt-oss-20b")

    if not api_key or os.getenv("MODEL_ENABLED", "true").lower() == "false":
        verdict = "scam" if rules_data["score"] >= 50 else "genuine"
        state["final"] = {
            "verdict": verdict,
            "category": "rule_fallback",
            "reason": f"Evaluated via rules (score {rules_data['score']}/100). LLM disabled.",
            "rules": rules_data
        }
        return state

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        # Enforce Pidgin or English based on frontend toggle
        lang_instruction = (
            "Write the 'reason' field strictly in natural Nigerian Pidgin English (e.g. 'Dis message na fake, no click the link oo')."
            if language == "pidgin"
            else "Write the 'reason' field in clear standard English."
        )

        prompt = f"""You are an expert fraud analyst evaluating SMS and messaging scams in Nigeria.
Language setting: {language.upper()}
Instruction: {lang_instruction}

Deterministic rule engine score: {rules_data['score']}/100.
Triggered rules: {json.dumps(rules_data['flags'])}
Message to evaluate: "{message}"

Return a JSON response with this exact structure:
{{
    "verdict": "scam" or "genuine",
    "category": "loan_scam", "bank_phishing", "legitimate_alert", or "general_phishing",
    "reason": "Clear explanation adhering to the requested language."
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
            "category": llm_result.get("category", "general_phishing"),
            "reason": llm_result.get("reason", f"Evaluated with rule score {rules_data['score']}/100."),
            "rules": rules_data
        }

    except Exception as e:
        verdict = "scam" if rules_data["score"] >= 50 else "genuine"
        state["final"] = {
            "verdict": verdict,
            "category": "fallback",
            "reason": f"Rule score {rules_data['score']}/100 (LLM error: {str(e)})",
            "rules": rules_data
        }

    return state