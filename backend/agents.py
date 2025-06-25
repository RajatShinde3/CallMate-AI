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
