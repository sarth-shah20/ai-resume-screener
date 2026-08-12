from io import BytesIO
from pathlib import Path
import fitz
from docx import Document

class DocumentParseError(ValueError):
    pass

def parse_document(filename: str, content: bytes, max_size_bytes: int) -> str:
    if not content:
        raise DocumentParseError("The uploaded document is empty.")
    if len(content) > max_size_bytes:
        raise DocumentParseError("The uploaded document exceeds the size limit.")
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt"}:
        raise DocumentParseError("Supported document types are PDF, DOCX, and TXT.")
    try:
        if suffix == ".pdf":
            with fitz.open(stream=content, filetype="pdf") as document:
                text = "\n".join(page.get_text("text") for page in document)
        elif suffix == ".docx":
            text = "\n".join(p.text for p in Document(BytesIO(content)).paragraphs)
        else:
            text = content.decode("utf-8-sig")
    except Exception as exc:
        raise DocumentParseError("The document is corrupt, encrypted, or unreadable.") from exc
    text = "\n".join(line.strip() for line in text.replace("\x00", "").splitlines() if line.strip())
    if not text:
        raise DocumentParseError("No extractable text was found. Scanned PDFs require OCR, which is not supported.")
    return text
