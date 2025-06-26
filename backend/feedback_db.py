# ──────────────────────────────────────────────
# 📁 feedback_db.py – SQLite Storage for Feedback
# ──────────────────────────────────────────────

import sqlite3
import pathlib

# Define the database path
DB = pathlib.Path("feedback.db")

# Set up SQLite connection
conn = sqlite3.connect(DB, check_same_thread=False)
cur = conn.cursor()

# Create table if it doesn't exist
cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        call_id TEXT,
        text TEXT,
        helpful INTEGER
    )
""")
conn.commit()

# Save feedback to database
def save_feedback_sql(call_id: str, text: str, helpful: bool):
    cur.execute(
        "INSERT INTO feedback (call_id, text, helpful) VALUES (?, ?, ?)",
        (call_id, text, int(helpful))
    )
    conn.commit()

# Summarize feedback counts (👍 and 👎)
def summary_sql():
    try:
        cur.execute("SELECT helpful, COUNT(*) FROM feedback GROUP BY helpful")
        rows = dict(cur.fetchall())  # {0: count, 1: count}
    except Exception:
        rows = {}
    return {
        "👍": rows.get(1, 0),
        "👎": rows.get(0, 0)
    }
