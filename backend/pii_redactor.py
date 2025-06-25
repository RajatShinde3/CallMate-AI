# backend/pii_redactor.py
import re

# ─────────────────────────────────────────────
# Precompiled PII Regex Patterns
# ─────────────────────────────────────────────
EMAIL_RE   = re.compile(r'\b[\w\.-]+?@\w+?\.\w+?\b', re.I)
CARD_RE    = re.compile(r'\b(?:\d[ -]*?){13,16}\b')
PHONE_RE   = re.compile(r'\b(?:\+?\d{1,3}[- ]?)?\d{10}\b')
NUMBER_RE  = re.compile(r'\b\d{6,}\b')         # 6+ digits (generic IDs)
NAME_RE    = re.compile(r'\b(Rajat\s+Shinde)\b', re.I)  # Replace with known names

# ─────────────────────────────────────────────
# Redaction Utility
# ─────────────────────────────────────────────
def redact(text: str) -> str:
    """Redacts common PII patterns and logs what was replaced."""
    found = {}

    def _sub(pattern, label):
        matches = pattern.findall(text)
        if matches:
            found[label] = matches
        return pattern.sub(f'[{label}]', text)

    text = _sub(EMAIL_RE,  'EMAIL')
    text = _sub(CARD_RE,   'CARD')
    text = _sub(PHONE_RE,  'PHONE')
    text = _sub(NUMBER_RE, 'NUMBER')
    text = _sub(NAME_RE,   'NAME')

    if found:
        print("🔐 Redacted PII →", found)   # Appears in uvicorn logs
    return text
