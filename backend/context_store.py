# Stores last N utterances per call_id (in-memory for demo)
from collections import defaultdict, deque

MAX_CONTEXT = 5
_CONTEXT = defaultdict(lambda: deque(maxlen=MAX_CONTEXT))

def add_utterance(call_id: str, text: str):
    _CONTEXT[call_id].append(text)

def get_context(call_id: str):
    return list(_CONTEXT[call_id])
