# backend/pii_redactor.py
import re
from typing import Tuple, Pattern, Dict

# --- Compile common PII regex patterns ----------------------------
_PATTERNS: Dict[str, Pattern] = {
    "EMAIL": re.compile(
        r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
    ),
    "PHONE": re.compile(
        # +1-555-555-5555 | (555) 555-5555 | 555-555-5555
        r"\b(?:\+?\d{1,3}[-.\s]?)?"
        r"(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"
    ),
    "CARD": re.compile(
        # 13-16 contiguous digits or separated by spaces
        r"\b(?:\d[ -]*?){13,16}\b"
    ),
}

_REPLACE_MAP = {
    "EMAIL": "[EMAIL]",
    "PHONE": "[PHONE]",
    "CARD": "[CARD]",
}


def redact(text: str) -> str:
    """Return a copy of *text* with PII replaced by tokens."""
    redacted = text
    for label, pattern in _PATTERNS.items():
        redacted = pattern.sub(_REPLACE_MAP[label], redacted)
    return redacted
