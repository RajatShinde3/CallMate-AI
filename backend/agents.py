import asyncio
import random
from typing import Tuple, List

# Utility: random confidence score between 80-97 %
def _rand_conf() -> float:
    return round(random.uniform(0.80, 0.97), 2)


# ─────────────────────────────────────────────────────────────
# Sentiment Agent  →  (sentiment_label, confidence)
# ─────────────────────────────────────────────────────────────
async def SentimentAgent(text: str) -> Tuple[str, float]:
    await asyncio.sleep(0.2)  # simulate latency
    tl = text.lower()

    if any(kw in tl for kw in ["not happy", "bad", "worst", "angry", "refund"]):
        return "negative", _rand_conf()
    if any(kw in tl for kw in ["great", "awesome", "thank you", "love"]):
        return "positive", _rand_conf()
    return "neutral", _rand_conf()


# ─────────────────────────────────────────────────────────────
# Knowledge Agent  →  (suggestion_text, confidence)
# ─────────────────────────────────────────────────────────────
async def KnowledgeAgent(text: str) -> Tuple[str, float]:
    await asyncio.sleep(0.3)
    tl = text.lower()

    if "refund" in tl:
        suggestion = "Apologize for the inconvenience and assure a quick refund resolution."
    elif "delay" in tl or "late" in tl:
        suggestion = "Assure the customer you will check shipment status immediately."
    else:
        suggestion = "Thank the customer and offer further help."

    return suggestion, _rand_conf()


# ─────────────────────────────────────────────────────────────
# Compliance Agent  →  (status, confidence)
# ─────────────────────────────────────────────────────────────
async def ComplianceAgent(text: str) -> Tuple[str, float]:
    await asyncio.sleep(0.2)
    tl = text.lower()
    flagged = any(kw in tl for kw in ["card", "cvv", "account number", "password"])
    return ("flagged" if flagged else "clean"), _rand_conf()


# ─────────────────────────────────────────────────────────────
# Escalation Agent (uses other agents’ outputs)
# ─────────────────────────────────────────────────────────────
async def EscalationAgent(sentiment: str, compliance: str) -> str:
    await asyncio.sleep(0.1)
    return "Recommended" if (sentiment == "negative" or compliance == "flagged") else "Not needed"


# ─────────────────────────────────────────────────────────────
# Summary Agent  (quick post-call recap)
# ─────────────────────────────────────────────────────────────
async def SummaryAgent(conversation: List[str]) -> str:
    await asyncio.sleep(0.2)
    if not conversation:
        return "No conversation to summarise."

    first = conversation[0][:60]
    last = conversation[-1][:60]
    return (
        f"The call began with: “{first} …” and ended with: “{last} …”. "
        f"Total turns: {len(conversation)}."
    )
