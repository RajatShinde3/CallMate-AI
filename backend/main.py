from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncio, time, json
from pathlib import Path
from backend.context_store import add_utterance, get_context
from backend.agents import (
    SentimentAgent,
    KnowledgeAgent,
    ComplianceAgent,
    EscalationAgent,
    SummaryAgent
)
from backend.pii_redactor import redact
from backend.feedback_db import save_feedback_sql as save_feedback
from backend.feedback_db import summary_sql as count_feedback

load_dotenv()

app = FastAPI(title="CallMate AI – Backend")

# ───────────────────────────────────────────────────────
# Input model
# ───────────────────────────────────────────────────────
class TranscriptChunk(BaseModel):
    text: str
    call_id: str

# ───────────────────────────────────────────────────────
# Root health check
# ───────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "backend up"}

# ───────────────────────────────────────────────────────
# Main Suggestion Endpoint
# ───────────────────────────────────────────────────────
@app.post("/suggest")
async def suggest(chunk: TranscriptChunk):
    safe_text = redact(chunk.text)
    add_utterance(chunk.call_id, safe_text)
    start_time = time.time()

    # Run agents concurrently
    (sentiment, s_conf), (suggestion, k_conf), (compliance, c_conf) = await asyncio.gather(
        SentimentAgent(safe_text),
        KnowledgeAgent(safe_text),
        ComplianceAgent(safe_text),
    )

    escalation = await EscalationAgent(sentiment, compliance)
    latency_ms = int((time.time() - start_time) * 1000)

    return {
    "suggestion": f"{suggestion} (via multi-agent)",
    "sentiment": sentiment,
    "compliance": compliance,
    "confidence": {
        "sentiment": s_conf,
        "knowledge": k_conf,
        "compliance": c_conf,
    },
    "escalation": escalation,
    "pii_redacted": safe_text != chunk.text,
    "redacted_text": safe_text,
    "latency_ms": latency_ms,
}


# ───────────────────────────────────────────────────────
# Consent Logging
# ───────────────────────────────────────────────────────
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

# ───────────────────────────────────────────────────────
# Feedback storage
# ───────────────────────────────────────────────────────
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

# ───────────────────────────────────────────────────────
# Post-call summary endpoint
# ───────────────────────────────────────────────────────
@app.get("/summary/{call_id}")
async def post_call_summary(call_id: str):
    context = get_context(call_id)
    summary = await SummaryAgent(context)
    overall_sentiment = "neutral"
    overall_compliance = "clean"

    if any("refund" in line.lower() or "angry" in line.lower() for line in context):
        overall_sentiment = "negative"

    if any("card" in line.lower() or "cvv" in line.lower() for line in context):
        overall_compliance = "flagged"

    escalation = "Recommended" if (
        overall_sentiment == "negative" or overall_compliance == "flagged"
    ) else "Not needed"

    return {
        "summary": summary,
        "sentiment_overall": overall_sentiment,
        "compliance_overall": overall_compliance,
        "escalation": escalation,
        "utterances": context
    }
