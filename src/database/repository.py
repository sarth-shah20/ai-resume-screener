import asyncio
import json
import sqlite3
from pathlib import Path

from src.models.schemas import (
    AnalyzeResponse,
    CandidateDashboardItem,
    CandidateResult,
    ExtractedJob,
    JobCandidatesResponse,
    JobDashboardItem,
)


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

    async def save(self, response: AnalyzeResponse, raw_job_description: str) -> None:
        await asyncio.to_thread(self._save, response, raw_job_description)

    async def list_jobs(self) -> list[JobDashboardItem]:
        return await asyncio.to_thread(self._list_jobs)

    async def list_candidates(self, job_id: str) -> JobCandidatesResponse | None:
        return await asyncio.to_thread(self._list_candidates, job_id)

    async def get_candidate(self, job_id: str, candidate_id: str) -> CandidateResult | None:
        return await asyncio.to_thread(self._get_candidate, job_id, candidate_id)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _save(self, response: AnalyzeResponse, raw_job_description: str) -> None:
        with self._connect() as connection:
            self._create_schema(connection)
            connection.execute(
                "INSERT INTO screening_requests (id, job_title, job_json, raw_description, warnings_json, processing_ms) VALUES (?, ?, ?, ?, ?, ?)",
                (response.request_id, response.job.title, response.job.model_dump_json(), raw_job_description, json.dumps(response.warnings), response.processing_ms),
            )
            connection.executemany(
                "INSERT INTO candidate_results (request_id, candidate_id, source_name, result_json) VALUES (?, ?, ?, ?)",
                [(response.request_id, candidate.candidate_id, candidate.source_name, candidate.model_dump_json()) for candidate in response.candidates],
            )

    def _list_jobs(self) -> list[JobDashboardItem]:
        with self._connect() as connection:
            self._create_schema(connection)
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT r.id AS job_id, r.job_title AS title, COUNT(c.id) AS candidate_count,
                       r.created_at AS latest_analysis_at,
                       COALESCE(AVG(json_extract(c.result_json, '$.verified_score')), 0) AS average_verified_score,
                       COALESCE(AVG(json_extract(c.result_json, '$.potential_score')), 0) AS average_potential_score
                FROM screening_requests r
                LEFT JOIN candidate_results c ON c.request_id = r.id
                GROUP BY r.id
                ORDER BY r.created_at DESC, r.rowid DESC
                """
            ).fetchall()
            return [JobDashboardItem.model_validate(dict(row)) for row in rows]

    def _list_candidates(self, job_id: str) -> JobCandidatesResponse | None:
        with self._connect() as connection:
            self._create_schema(connection)
            connection.row_factory = sqlite3.Row
            job = connection.execute(
                "SELECT job_json, raw_description FROM screening_requests WHERE id = ?", (job_id,)
            ).fetchone()
            if job is None:
                return None
            rows = connection.execute(
                "SELECT candidate_id, source_name, result_json, created_at AS analyzed_at FROM candidate_results WHERE request_id = ? ORDER BY created_at DESC, id DESC",
                (job_id,),
            ).fetchall()
            candidates = []
            for row in rows:
                result = CandidateResult.model_validate_json(row["result_json"])
                candidates.append(
                    CandidateDashboardItem(
                        candidate_id=result.candidate_id,
                        source_name=result.source_name,
                        verified_score=result.verified_score,
                        potential_score=result.potential_score,
                        fit_band=result.fit_band,
                        summary=result.summary,
                        github_project_count=len(result.github_projects),
                        analyzed_at=row["analyzed_at"],
                    )
                )
            return JobCandidatesResponse(
                job_id=job_id,
                job=ExtractedJob.model_validate_json(job["job_json"]),
                raw_description=job["raw_description"],
                candidates=candidates,
            )

    def _get_candidate(self, job_id: str, candidate_id: str) -> CandidateResult | None:
        with self._connect() as connection:
            self._create_schema(connection)
            row = connection.execute(
                "SELECT result_json FROM candidate_results WHERE request_id = ? AND candidate_id = ?",
                (job_id, candidate_id),
            ).fetchone()
            return CandidateResult.model_validate_json(row[0]) if row else None

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS screening_requests (
                id TEXT PRIMARY KEY,
                job_title TEXT NOT NULL,
                job_json TEXT NOT NULL,
                raw_description TEXT NOT NULL DEFAULT '',
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
        columns = {row[1] for row in connection.execute("PRAGMA table_info(screening_requests)")}
        if "raw_description" not in columns:
            connection.execute("ALTER TABLE screening_requests ADD COLUMN raw_description TEXT NOT NULL DEFAULT ''")
