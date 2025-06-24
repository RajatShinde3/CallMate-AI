from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()  # pulls in .env AWS keys

app = FastAPI(title="CallMate AI – Backend")

class TranscriptChunk(BaseModel):
    text: str
    call_id: str

@app.get("/")
async def root():
    return {"status": "backend up"}

@app.post("/suggest")
async def suggest(chunk: TranscriptChunk):
    """
    FIRST PASS:
    • simply echoes a dummy suggestion.
    • we’ll wire in Bedrock later.
    """
    # TODO: call real GenAI
    return {
        "suggestion": f"Thanks for sharing, {chunk.text[:20]}...",
        "sentiment": "neutral"
    }
