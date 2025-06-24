from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from backend.bedrock_service import gen_suggestion

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
    try:
        gen = gen_suggestion(chunk.text)
        return gen
    except Exception as e:
        return {"error": str(e)}
