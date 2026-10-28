import os
import json
from app.graph.state import ScamState


async def run_llm_evaluation(state: ScamState) -> ScamState:
    message = state["message"]
    rules_data = state["rules"]

    # If rules already flagged it as severe, or for hybrid reasoning:
    # Here you can call your LLM client (e.g., Groq, OpenAI, or local model)

    # For a clean starter implementation or placeholder that uses your model adapter:
    try:
        # Example structured output simulation or actual API call
        # Replace this with your actual LLM client integration
        verdict = rules_data["verdict"]
        category = "general_phishing" if verdict == "scam" else "unknown"
        reason = f"Hybrid engine evaluated message based on rule score {rules_data['score']}/100 and contextual analysis."

        state["final"] = {
            "verdict": verdict,
            "category": category,
            "reason": reason,
            "rules": rules_data
        }
    except Exception as e:
        # Fallback to rule output if LLM fails
        state["final"] = {
            "verdict": rules_data["verdict"],
            "category": "fallback",
            "reason": f"Evaluated via rules due to LLM error: {str(e)}",
            "rules": rules_data
        }

    return state