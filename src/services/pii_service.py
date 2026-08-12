import re
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")
LINKEDIN = re.compile(r"https?://(?:www\.)?linkedin\.com/\S+", re.IGNORECASE)
def redact_pii(text: str) -> str:
    return LINKEDIN.sub("[LINKEDIN REDACTED]", PHONE.sub("[PHONE REDACTED]", EMAIL.sub("[EMAIL REDACTED]", text)))
