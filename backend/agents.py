import asyncio
import random

# Simulated agent that classifies sentiment
async def SentimentAgent(text: str) -> str:
    await asyncio.sleep(0.2)
    if any(w in text.lower() for w in ["not happy", "bad", "worst", "angry", "refund"]):
        return "negative"
    elif any(w in text.lower() for w in ["great", "awesome", "thank you"]):
        return "positive"
    return "neutral"

# Simulated agent that retrieves a response
async def KnowledgeAgent(text: str) -> str:
    await asyncio.sleep(0.3)
    return (
        "Apologize for the inconvenience and assure quick resolution."
        if "refund" in text.lower()
        else "Thank the customer and offer help with anything else."
    )

# Simulated compliance agent
async def ComplianceAgent(text: str) -> str:
    await asyncio.sleep(0.2)
    flagged = any(word in text.lower() for word in ["card", "cvv", "account number"])
    return "flagged" if flagged else "clean"

# add escalation and summary helpers
async def EscalationAgent(sentiment: str, compliance: str) -> str:
    await asyncio.sleep(0.1)
    return "Recommended" if sentiment == "negative" or compliance == "flagged" else "Not needed"

async def SummaryAgent(conversation: list[str]) -> str:
    """Returns a quick summary string (mocked)."""
    await asyncio.sleep(0.2)
    if not conversation:
        return "No conversation to summarise."
    first, last = conversation[0], conversation[-1]
    return f"The call began with: '{first[:40]}…' and ended with: '{last[:40]}…'"
