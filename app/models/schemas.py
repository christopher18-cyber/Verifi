from typing import Literal
from pydantic import BaseModel, Field

Verdict = Literal["scam", "suspicious", "genuine"]
Confidence = Literal["low", "medium", "high"]
Category = Literal[
    "fake_bank_alert", "prize_and_fee", "loan_app_threat", "fake_job",
    "fake_relative", "investment", "delivery", "other_scam", "genuine",
]

class Analysis(BaseModel):
    verdict: Verdict
    confidence: Confidence
    category: Category
    what_sender_wants: str
    tactics: list[str] = Field(default_factory=list)
    quotes: list[str] = Field(default_factory=list)
    reason: str