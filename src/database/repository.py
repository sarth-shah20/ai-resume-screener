import asyncio
import json
import sqlite3
from pathlib import Path

from src.models.schemas import AnalyzeResponse


class ScreeningRepository:
    """SQLite persistence for completed, privacy-safe screening responses."""

    def __init__(self, database_url: str):
        prefix = "sqlite:///"
        if not database_url.startswith(prefix):
            raise ValueError("Only sqlite:/// database URLs are supported.")
        value = database_url[len(prefix) :]
        if not value:
            raise ValueError("SQLite database path cannot be empty.")
        self.path = Path(value)

    async def save(self, response: AnalyzeResponse) -> None:
        await asyncio.to_thread(self._save, response)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _save(self, response: AnalyzeResponse) -> None:
        with self._connect() as connection:
            self._create_schema(connection)
            connection.execute(
                "INSERT INTO screening_requests (id, job_title, job_json, warnings_json, processing_ms) VALUES (?, ?, ?, ?, ?)",
                (response.request_id, response.job.title, response.job.model_dump_json(), json.dumps(response.warnings), response.processing_ms),
            )
            connection.executemany(
                "INSERT INTO candidate_results (request_id, candidate_id, source_name, result_json) VALUES (?, ?, ?, ?)",
                [(response.request_id, candidate.candidate_id, candidate.source_name, candidate.model_dump_json()) for candidate in response.candidates],
            )

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS screening_requests (
                id TEXT PRIMARY KEY,
                job_title TEXT NOT NULL,
                job_json TEXT NOT NULL,
                warnings_json TEXT NOT NULL,
                processing_ms INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS candidate_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                candidate_id TEXT NOT NULL,
                source_name TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(request_id, candidate_id),
                FOREIGN KEY(request_id) REFERENCES screening_requests(id) ON DELETE CASCADE
            );
            """
        )
