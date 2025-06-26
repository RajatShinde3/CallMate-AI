# backend/feedback_store.py

import json
from pathlib import Path
from datetime import datetime

# Path to the feedback storage file
FILE_PATH = Path("feedback.json")

# Save a new feedback entry with timestamp
def save_feedback(call_id: str, text: str, helpful: bool):
    feedback = load_feedback()
    feedback.append({
        "call_id": call_id,
        "text": text,
        "helpful": helpful,
        "timestamp": datetime.utcnow().isoformat()  # Add UTC timestamp
    })
    FILE_PATH.write_text(json.dumps(feedback, indent=2))


# Load all feedback entries from file
def load_feedback():
    if FILE_PATH.exists():
        return json.loads(FILE_PATH.read_text())
    return []


# Count summary of 👍 / 👎 feedback
def count_feedback() -> dict:
    feedback = load_feedback()
    helpful = sum(1 for f in feedback if f.get("helpful"))
    not_helpful = sum(1 for f in feedback if not f.get("helpful"))
    return {"👍": helpful, "👎": not_helpful}


# Return all feedback including timestamps (used for graph in dashboard)
def load_feedback_history():
    return load_feedback()
