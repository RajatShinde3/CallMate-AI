# backend/feedback_store.py
import json
from pathlib import Path

FILE_PATH = Path("feedback.json")

def save_feedback(call_id: str, text: str, helpful: bool):
    feedback = load_feedback()
    feedback.append({
        "call_id": call_id,
        "text": text,
        "helpful": helpful
    })
    FILE_PATH.write_text(json.dumps(feedback, indent=2))

def load_feedback():
    if FILE_PATH.exists():
        return json.loads(FILE_PATH.read_text())
    return []

def count_feedback() -> dict:
    feedback = load_feedback()
    helpful = sum(1 for f in feedback if f["helpful"])
    not_helpful = sum(1 for f in feedback if not f["helpful"])
    return {"👍": helpful, "👎": not_helpful}
