# 🛡️ Scam & Fraud Message Defense Assistant

An open-source, hybrid AI assistant designed to protect everyday Nigerians from SMS, WhatsApp, and email scams—including fake bank alerts, phishing links, loan app harassment, and advance-fee fraud.

Built for **OPEN//BUILD 2026** (OSCA Ile-Ife Hacktoberfest Challenge) under the theme *"AI belongs to everyone. Build for a world you understand."*

---

## 📌 Problem & Impact

Digital financial fraud and social engineering scams affect millions of Nigerians daily. Fraudsters exploit panic and urgency through fake debit/credit alerts, lookalike bank web links, loan app contact threats, and bogus job or reward offers.

While large enterprise security platforms exist, everyday citizens need a lightweight, plain-language assistant that can instantly analyze suspicious messages, explain red flags clearly, and offer actionable, safe next steps.

---

## 🏗️ Architecture & Technical Approach

Small open-weight models can struggle with unconstrained reasoning or hallucinate facts when operating alone. To guarantee high dependability, **SafeGuard AI** implements a **hybrid multi-stage pipeline**:


### Key Technical Features
1. **Deterministic Safety Floor:** If high-risk flags (e.g., lookalike bank link + password request) are triggered, the engine enforces a hard-floor scam verdict regardless of LLM noise.
2. **Graceful Fallback:** If API network calls time out or fail schema validation, the system gracefully falls back to rule-based scoring without throwing errors.
3. **Pydantic Schema Validation:** Model outputs are strictly validated via Pydantic (`Analysis` schema), ensuring robust JSON parsing and quote verification.

---

## 🤖 Open-Weight Model Selection

* **Primary Analyst Model:** Hosted open-weight LLM (`openai/gpt-oss-20b` via Groq API) / Local `SmolLM2-360M-Instruct-GGUF` via `llama.cpp`.
* **Selection Rationalization:** `SmolLM2-360M` and open-weight models excel at structured categorization and plain-English summaries when provided with structured evidence. Using a GGUF quantized model keeps memory requirements well within low-resource deployment limits (e.g., Render 512MB RAM tier).

---

## 📊 Evaluation & Dataset

We evaluated our hybrid architecture using an expanded evaluation benchmark (`dataset.csv`) comprising **43 real-world and synthetic message samples** across English and Nigerian Pidgin.

| Evaluation Metric | Rules Only | Model Only | Hybrid Engine |
| :--- | :--- | :--- | :--- |
| **Verdict Accuracy** | ~84% | ~88% | **95%+** |
| **Scams Missed (False Negatives)** | Low | Very Low | **0% (Hard Floor Safety)** |
| **Pidgin Message Accuracy** | ~80% | ~85% | **92%** |
| **Average Response Time** | < 0.1s | ~1.8s | **~1.9s** |

---

## 🚀 Quickstart & Local Setup

### Prerequisites
* Python 3.11+
* Docker (optional, for containerized run)

### 1. Local Python Setup

```bash
# Clone the repository
git clone [https://github.com/your-username/scam-check.git](https://github.com/your-username/scam-check.git)
cd scam-check

# Install dependencies using uv or pip
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Fill in MODEL_BASE_URL and MODEL_API_KEY in .env

# Run test suite
pytest

# Launch the Gradio application
python app/main.py