import pytest
from src.parsers import DocumentParseError, parse_document

def test_txt_parser():
    assert parse_document("resume.txt", b"Python developer", 1000) == "Python developer"

def test_rejects_empty_and_unsupported_documents():
    with pytest.raises(DocumentParseError):
        parse_document("resume.txt", b"", 1000)
    with pytest.raises(DocumentParseError):
        parse_document("resume.exe", b"content", 1000)
