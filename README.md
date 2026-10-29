# 🛡️ Scam & Fraud Message Defense Assistant

An open-weight AI and rule-augmented security engine designed to protect everyday users from social engineering attacks, fake bank alerts, loan-app harassment, and phishing attempts—with native support for local context and West African Pidgin nuances.

---

## 📌 Overview

Digital financial fraud across mobile messaging channels (SMS, WhatsApp, Email) heavily targets users through high-pressure tactics, fake debit/credit notifications, lookalike domains, and local slang. Standard filters often fail to flag these context-rich, localized threats.

The **Scam & Fraud Message Defense Assistant** addresses this by combining deterministic, rule-based scanning with an open-weight Large Language Model (LLM) pipeline powered by **LangGraph**. This hybrid approach guarantees instant detection of hardcoded risk indicators (like lookalike domains or sensitive data requests) while leveraging AI contextual reasoning for nuanced threats.

---

## 🏗️ Architecture & Workflow

The system is built on a decoupled, production-ready architecture:

```text
[ User Input / Client UI ]
           │
           ▼
 [ FastAPI (`/api/check`) ]
           │
           ▼
  [ LangGraph Pipeline ]
     ├── 1. Rules Node   ──────▶ (Deterministic checks: Regex, domain lookalikes, urgency flags)
     └── 2. LLM Node     ──────▶ (Contextual analysis, language nuance, confidence scoring)
           │
           ▼
 [ JSON Verdict Response ]

FastAPI Backend: Exposes a structured POST /api/check endpoint, handling asynchronous pipeline execution and serving the static frontend assets.

LangGraph Pipeline: Orchestrates a stateful evaluation flow:

Rules Node: Runs pattern matching for high-risk signals (BVN, OTP, PIN requests, phishing URLs, coercive language).

LLM Node: Evaluates intent, tone, and language context (English & Pidgin) when deterministic rules require deeper contextual reasoning.

🚀 Key Features
Hybrid Evaluation Engine: Combines speed and zero-false-negative reliability from rule checks with deep semantic comprehension from open-weight models.

Localized Context Awareness: Native detection for regional financial scams, loan-app contact shaming, and Pidgin social engineering.

Explainable Verdicts: Provides a risk score (0–100), highlighted threat signals, and a plain-language explanation with recommended safe next steps.

Production-Ready Deployment: Configured for Docker, containerized hosting, and Hugging Face Spaces deployment.


## 📂 Project Structure

```text
scam-check/
├── app/
│   ├── graph/
│   │   ├── nodes/
│   │   │   ├── llm_node.py    # LLM evaluation & contextual reasoning node
│   │   │   └── rules_node.py  # Deterministic pattern & rule matching node
│   │   ├── __init__.py
│   │   ├── build.py           # LangGraph state machine assembly
│   │   └── state.py           # TypedDict state schema definition
│   ├── models/
│   │   ├── adapter.py         # LLM provider adapter
│   │   └── schemas.py         # Request/Response Pydantic models
│   ├── prompts/               # Core system prompts (analyst, critic, explain)
│   ├── rules/                 # Pattern checking utilities & domain lists
│   └── main.py                # FastAPI application entrypoint
├── static/                    # Static frontend assets (HTML, CSS, JS)
├── eval/                      # Dataset evaluation scripts and test suites
├── Dockerfile                 # Production container definition
├── requirements.txt           # Dependencies manifest
└── README.md                  # Project documentation



🛠️ API Reference
Check Message
Evaluates a text message against the hybrid defense pipeline.

Endpoint: POST /api/check

Content-Type: application/json

Request Body
JSON
{
  "message": "GTBank Alert: Your account has been suspended. Verify your BVN immediately at [http://gtb-secure-verify.xyz/login](http://gtb-secure-verify.xyz/login)",
  "language": "en"
}

Response Body
JSON
{
  "verdict": "scam",
  "category": "fake_bank_alert",
  "reason": "The message uses coercive language regarding account suspension and directs the recipient to an unverified lookalike domain requesting sensitive financial credentials.",
  "rules": {
    "score": 80,
    "flags": [
      {
        "id": "sensitive_info",
        "label": "Requests Sensitive Information (BVN/OTP/PIN)",
        "weight": 40
      },
      {
        "id": "lookalike_domain",
        "label": "Lookalike / Phishing Domain Detected",
        "weight": 40
      }
    ]
  }
}


💻 Local Development Setup
Prerequisites
Python 3.11+

uv (recommended) or standard pip

Installation & Execution
1.  Clone the repository:

git clone [https://github.com/your-repo/scam-check.git](https://github.com/your-repo/scam-check.git)
cd scam-check

2.  Set up the virtual environment:

uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt


3.  Configure Environment Variables:
Create a .env file in the root directory:


PORT=8001
GROQ_API_KEY=your_api_key_here

4.   Run the FastAPI server:

uv run python -m app.main

5.   Access the Application:

Web UI: Open http://localhost:8001 (or the port logged in the console)

Interactive API Docs (Swagger): Open http://localhost:8001/docs

🐳 Docker & Hugging Face Deployment
Build and run locally using Docker:

docker build -t scam-check .
docker run -p 7860:7860 -e GROQ_API_KEY="your_api_key" scam-check

For Hugging Face Spaces:

Create a new Docker Space.

Push this repository to the Space remote.

Add your environment secrets (GROQ_API_KEY, etc.) in the Space settings under Variables and secrets.

📜 License
Distributed under the MIT License. See LICENSE for details.