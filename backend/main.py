# backend/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from fastapi import Request
from pathlib import Path
import json

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
from backend.agents import SentimentAgent, KnowledgeAgent, ComplianceAgent
import time
import asyncio 

@app.post("/suggest")
async def suggest(chunk: TranscriptChunk):
    safe_text = redact(chunk.text)
    start_time = time.time()

    # Run agents in parallel
    sentiment_task = SentimentAgent(safe_text)
    suggestion_task = KnowledgeAgent(safe_text)
    compliance_task = ComplianceAgent(safe_text)

    sentiment, suggestion, compliance = await asyncio.gather(
        sentiment_task, suggestion_task, compliance_task
    )

    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "suggestion": suggestion + f" (via multi-agent)",
        "sentiment": sentiment,
        "compliance": compliance,
        "pii_redacted": safe_text != chunk.text,
        "latency_ms": latency_ms
    }


CONSENT_FILE = Path("consent_log.json")

def save_consent(call_id: str, consent: bool):
    log = []
    if CONSENT_FILE.exists():
        log = json.loads(CONSENT_FILE.read_text())
    log.append({"call_id": call_id, "consent": consent})
    CONSENT_FILE.write_text(json.dumps(log, indent=2))

@app.post("/consent")
async def consent(call_id: str, consent: bool):
    save_consent(call_id, consent)
    return {"message": "Consent stored"}

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

from backend.feedback_store import save_feedback, count_feedback
from pydantic import BaseModel

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
