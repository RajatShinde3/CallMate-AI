# backend/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from fastapi import Request
from backend.feedback_store import save_feedback, count_feedback
# When credits arrive, uncomment the next import and swap logic
# from backend.bedrock_service import gen_suggestion

# NEW ― our redaction helper
from backend.pii_redactor import redact   # make sure pii_redactor.py exists

load_dotenv()  # pulls in .env AWS keys

app = FastAPI(title="CallMate AI – Backend")

class TranscriptChunk(BaseModel):
    text: str
    call_id: str

@app.get("/")
async def root():
    return {"status": "backend up"}

# ------------------------------------------------------------------
# MAIN ENDPOINT
# ------------------------------------------------------------------
@app.post("/suggest")
async def suggest(chunk: TranscriptChunk):
    """
    1. Redact PII from the incoming transcript
    2. (Temporary) generate a mock suggestion
    3. Return sentiment + redaction flag
    """
    # 1️⃣  PII redaction
    safe_text = redact(chunk.text)

    # 2️⃣  MOCK suggestion while waiting for Bedrock credits
    suggestion = (
        f"Apologize for the delay and assure action – based on: "
        f"{safe_text[:40]}..."
    )

    # 3️⃣  Assemble response (add 'pii_redacted' so UI can show badge)
    return {
        "suggestion": suggestion,
        "sentiment": "neutral",
        "pii_redacted": safe_text != chunk.text
    }

    # ----------------------------------------------------------------
    # 🔄 Once you have Bedrock access, replace section above with:
    #
    # try:
    #     result = gen_suggestion(safe_text)   # passes redacted text
    #     result["pii_redacted"] = safe_text != chunk.text
    #     return result
    # except Exception as e:
    #     return {"error": str(e)}
    # ----------------------------------------------------------------
class FeedbackItem(BaseModel):
    call_id: str
    text: str
    helpful: bool

@app.post("/feedback")
async def feedback(item: FeedbackItem):
    save_feedback(item.call_id, item.text, item.helpful)
    return {"message": "Feedback recorded"}

@app.get("/feedback/summary")
async def feedback_summary():
    return count_feedback()