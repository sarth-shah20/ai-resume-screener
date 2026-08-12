import httpx
import pytest

from app.services.screening_client import (
    BackendRequestError,
    ScreeningClient,
    Upload,
)


def test_client_maps_analysis_form_to_backend(monkeypatch):
    captured = {}

    def request(method, url, **kwargs):
        captured.update(method=method, url=url, **kwargs)
        return httpx.Response(
            200,
            request=httpx.Request(method, url),
            json={"request_id": "job-1", "candidates": []},
        )

    monkeypatch.setattr(httpx, "request", request)
    client = ScreeningClient("http://backend.test")
    result = client.analyze(
        job_text="Need Python",
        job_file=None,
        resume_text=None,
        resume_files=[Upload("resume.txt", b"Python", "text/plain")],
        blind_mode=True,
    )

    assert result["request_id"] == "job-1"
    assert captured["url"] == "http://backend.test/api/v1/analyze"
    assert captured["data"] == {"blind_mode": "true", "jd_text": "Need Python"}
    assert captured["files"][0][0] == "resume_files"


def test_client_surfaces_backend_detail(monkeypatch):
    def request(method, url, **kwargs):
        return httpx.Response(
            422,
            request=httpx.Request(method, url),
            json={"detail": "Provide at least one resume."},
        )

    monkeypatch.setattr(httpx, "request", request)
    with pytest.raises(BackendRequestError, match="Provide at least one resume"):
        ScreeningClient("http://backend.test").list_jobs()
