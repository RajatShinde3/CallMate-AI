import sqlite3
import pathlib

DB = pathlib.Path("feedback.db")
conn = sqlite3.connect(DB, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        call_id TEXT,
        text TEXT,
        helpful INTEGER
    )
""")
conn.commit()

def save_feedback_sql(call_id: str, text: str, helpful: bool):
    cur.execute(
        "INSERT INTO feedback (call_id, text, helpful) VALUES (?, ?, ?)",
        (call_id, text, int(helpful))
    )
    conn.commit()

def summary_sql():
    cur.execute("SELECT helpful, COUNT(*) FROM feedback GROUP BY helpful")
    rows = dict(cur.fetchall())  # {0: count, 1: count}
    return {"👍": rows.get(1, 0), "👎": rows.get(0, 0)}
