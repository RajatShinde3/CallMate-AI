from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import asyncio, time, json

# Internal modules
from backend.pii_redactor import redact
from backend.context_store import add_utterance, get_context
from backend.feedback_store import save_feedback, count_feedback
from backend.agents import (
    SentimentAgent, KnowledgeAgent, ComplianceAgent,
    EscalationAgent, SummaryAgent
)

# Optional (for future Bedrock swap)
# from backend.bedrock_service import gen_suggestion

load_dotenv()

app = FastAPI(title="CallMate AI – Backend")

# ─────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────

class TranscriptChunk(BaseModel):
    text: str
    call_id: str

class FeedbackItem(BaseModel):
    call_id: str
    text: str
    helpful: bool

# ─────────────────────────────────────────────
# Root Health Check
# ─────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "backend up"}

# ─────────────────────────────────────────────
# Suggestion Endpoint (Main AI Call)
# ─────────────────────────────────────────────

@app.post("/suggest")
async def suggest(chunk: TranscriptChunk):
    safe_text = redact(chunk.text)
    add_utterance(chunk.call_id, safe_text)
    start_time = time.time()

    # Run multi-agent tasks in parallel
    sentiment_task  = SentimentAgent(safe_text)
    suggest_task    = KnowledgeAgent(safe_text)
    compliance_task = ComplianceAgent(safe_text)

    sentiment, suggestion, compliance = await asyncio.gather(
        sentiment_task, suggest_task, compliance_task
    )

    escalation = await EscalationAgent(sentiment, compliance)
    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "suggestion": suggestion + " (via multi-agent)",
        "sentiment": sentiment,
        "compliance": compliance,
        "escalation": escalation,
        "pii_redacted": safe_text != chunk.text,
        "latency_ms": latency_ms
    }

# ─────────────────────────────────────────────
# Feedback Storage
# ─────────────────────────────────────────────

@app.post("/feedback")
async def feedback(item: FeedbackItem):
    save_feedback(item.call_id, item.text, item.helpful)
    return {"message": "Feedback recorded"}

@app.get("/feedback/summary")
async def feedback_summary():
    return count_feedback()

# ─────────────────────────────────────────────
# Consent Logging
# ─────────────────────────────────────────────

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

# ─────────────────────────────────────────────
# Call Summary Report
# ─────────────────────────────────────────────

@app.get("/summary/{call_id}")
async def summary(call_id: str):
    convo = get_context(call_id)
    sentiment_overall = "negative" if any("not happy" in c.lower() or "bad" in c.lower() for c in convo) else "neutral"
    compliance_overall = "flagged" if any("card" in c.lower() or "email" in c.lower() for c in convo) else "clean"
    text_summary = await SummaryAgent(convo)
    escalation = await EscalationAgent(sentiment_overall, compliance_overall)

    return {
        "summary": text_summary,
        "sentiment_overall": sentiment_overall,
        "compliance_overall": compliance_overall,
        "escalation": escalation,
        "utterances": convo
    }

# ─────────────────────────────────────────────
# Bedrock integration placeholder (future)
# ─────────────────────────────────────────────

# Replace /suggest logic with Bedrock when credits come:
# try:
#     result = gen_suggestion(safe_text)
#     result["pii_redacted"] = safe_text != chunk.text
#     return result
# except Exception as e:
#     return {"error": str(e)}
