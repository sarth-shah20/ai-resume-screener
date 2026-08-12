"""Typed HTTP facade between Streamlit and FastAPI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from src.config import Settings


class BackendUnavailable(RuntimeError):
    pass


class BackendRequestError(RuntimeError):
    pass


@dataclass(frozen=True)
class Upload:
    filename: str
    content: bytes
    content_type: str


class ScreeningClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or Settings().backend_url).rstrip("/")

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = httpx.request(
                method, f"{self.base_url}{path}", timeout=180, **kwargs
            )
        except httpx.HTTPError as exc:
            raise BackendUnavailable(
                f"Could not connect to the screening backend at {self.base_url}."
            ) from exc
        if response.is_error:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise BackendRequestError(str(detail))
        return response.json()

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def analyze(
        self,
        *,
        job_text: str | None,
        job_file: Upload | None,
        resume_text: str | None,
        resume_files: list[Upload],
        blind_mode: bool,
    ) -> dict[str, Any]:
        data: dict[str, str] = {"blind_mode": str(blind_mode).lower()}
        files: list[tuple[str, tuple[str, bytes, str]]] = []
        if job_text:
            data["jd_text"] = job_text
        if job_file:
            files.append(
                ("jd_file", (job_file.filename, job_file.content, job_file.content_type))
            )
        if resume_text:
            data["resume_text"] = resume_text
        files.extend(
            ("resume_files", (item.filename, item.content, item.content_type))
            for item in resume_files
        )
        return self._request("POST", "/api/v1/analyze", data=data, files=files)

    def list_jobs(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/jobs")

    def list_candidates(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/jobs/{job_id}/candidates")

    def get_candidate(self, job_id: str, candidate_id: str) -> dict[str, Any]:
        return self._request(
            "GET", f"/api/v1/jobs/{job_id}/candidates/{candidate_id}"
        )


def get_client() -> ScreeningClient:
    return ScreeningClient()
