import os, json, time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["MODEL_BASE_URL"],
    api_key=os.environ["MODEL_API_KEY"],
    timeout=float(os.environ.get("REQUEST_TIMEOUT_SECONDS", 30)),
)

SYSTEM = (
    "You are a scam-detection analyst for Nigerian SMS, WhatsApp and email messages. "
    "Reply with JSON only, no other text, using exactly these keys: "
    '"verdict" (scam, suspicious or genuine), '
    '"confidence" (low, medium or high), '
    '"category" (short label), '
    '"what_sender_wants" (one sentence), '
    '"reason" (one or two sentences).'
)

MESSAGES = [
    "GTBank Alert: Your account has been suspended. Verify your BVN and OTP within 24 hours: http://gtb-secure-verify.xyz/login",
    "Debit alert: N5,000.00 left your account on 24-Oct. Never share your OTP or PIN with anyone, including bank staff.",
    "Hi, we are hiring remote data entry staff. Earn N150,000 weekly. Send N3,500 registration fee to start today.",
    "Oga, your account don block o. Send your OTP make we fit open am back.",
]

for msg in MESSAGES:
    start = time.time()
    resp = client.chat.completions.create(
        model=os.environ["MODEL_NAME"],
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": msg},
        ],
        temperature=0,
        max_tokens=300,
    )
    text = resp.choices[0].message.content
    secs = time.time() - start
    print("\nMESSAGE:", msg[:70])
    print(f"TIME: {secs:.1f}s")
    try:
        print("PARSED:", json.loads(text))
    except Exception:
        print("NOT VALID JSON:", text)