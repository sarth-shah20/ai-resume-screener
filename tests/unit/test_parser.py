import pytest
from src.parsers import DocumentParseError, extract_github_repositories, parse_document

def test_txt_parser():
    assert parse_document("resume.txt", b"Python developer", 1000) == "Python developer"

def test_rejects_empty_and_unsupported_documents():
    with pytest.raises(DocumentParseError):
        parse_document("resume.txt", b"", 1000)
    with pytest.raises(DocumentParseError):
        parse_document("resume.exe", b"content", 1000)

def test_extracts_and_normalizes_github_repository_urls():
    text = "Code: https://github.com/example/project.git and profile https://github.com/example"
    assert extract_github_repositories("resume.txt", text.encode(), text) == [
        "https://github.com/example/project"
    ]
