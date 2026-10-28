import asyncio
from app.models.adapter import analyse

msgs = [
    "GTBank Alert: Your account has been suspended. Verify your BVN and OTP within 24 hours: http://gtb-secure-verify.xyz/login",
    "Debit alert: N5,000.00 left your account on 24-Oct. Never share your OTP or PIN with anyone.",
    "Mummy it's me, I lost my phone, this is my new number. Please send 20k airtime urgently.",
]

async def main():
    for m in msgs:
        print(await analyse(m, {}), "\n")

asyncio.run(main())