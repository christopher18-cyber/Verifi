import os
import json
from openai import AsyncOpenAI
from app.graph.state import ScamState


async def run_llm_evaluation(state: ScamState) -> ScamState:
    message = state["message"]
    rules_data = state["rules"]

    api_key = os.getenv("MODEL_API_KEY")
    base_url = os.getenv("MODEL_BASE_URL", "https://api.groq.com/openai/v1")
    model_name = os.getenv("MODEL_NAME", "openai/gpt-oss-20b")

    # If API key is missing or disabled, fall back to rule verdict
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

        prompt = f"""You are an expert fraud analyst evaluating SMS and messaging scams.

        Here are examples of how to categorize messages based on real threat data:
        - "GTBank Alert: Your account is suspended. Verify BVN here: http://..." -> SCAM (bank_phishing)
        - "N200,000 loan approved instantly without collateral. Click link: http://..." -> SCAM (loan_scam)
        - "Debit alert: N5,000 left your account. Never share your OTP or PIN with anyone." -> GENUINE (legitimate_alert)

        Now analyze this message:
        Deterministic rule engine score: {rules_data['score']}/100.
        Triggered rules: {json.dumps(rules_data['flags'])}
        Message to evaluate: "{message}"

        Return a JSON response with this structure:
        {{
            "verdict": "scam" or "genuine",
            "category": "loan_scam", "bank_phishing", "legitimate_alert", or "general_phishing",
            "reason": "Clear explanation in plain words."
        }}
        """

        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a fraud detection assistant that outputs strict JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
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
        # Fallback if Groq API call fails
        verdict = "scam" if rules_data["score"] >= 50 else "genuine"
        state["final"] = {
            "verdict": verdict,
            "category": "fallback",
            "reason": f"Rule score {rules_data['score']}/100 (LLM error: {str(e)})",
            "rules": rules_data
        }

    return state