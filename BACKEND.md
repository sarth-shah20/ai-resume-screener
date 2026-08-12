# FastAPI Backend

## Start locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn app.api:app --reload
```

Replace `.env` contents with:

```env
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=openai/gpt-oss-120b
GITHUB_TOKEN=
DATABASE_URL=sqlite:///data/resume_screener.db
MAX_FILE_SIZE_MB=5
MAX_RESUMES_PER_REQUEST=5
MAX_CONCURRENT_EVALUATIONS=3
LLM_TIMEOUT_SECONDS=90
```

API documentation is available at `http://127.0.0.1:8000/docs`.

## Start the recruiter interface

In a second terminal, with the backend still running:

```bash
streamlit run app/main.py
```

The interface is available at `http://127.0.0.1:8501` and uses
`BACKEND_URL=http://127.0.0.1:8000` by default.

`POST /api/v1/analyze` accepts a job description and up to five resumes as text, PDF, DOCX, or TXT. `POST /api/v1/github/verify` performs optional, read-only verification of one canonical public GitHub repository URL.

Completed analyses are persisted to SQLite. Candidate evaluations run concurrently while `MAX_CONCURRENT_EVALUATIONS` bounds NVIDIA API usage. Canonical public GitHub repository links in resume text and PDF hyperlinks are verified concurrently and included in each candidate's `github_projects`.

Recruiter dashboard APIs:

- `GET /api/v1/jobs` lists saved job analyses newest first with candidate counts and average scores.
- `GET /api/v1/jobs/{job_id}/candidates` returns the JD and its candidates newest first.
- `GET /api/v1/jobs/{job_id}/candidates/{candidate_id}` returns the candidate's complete report, including GitHub verification.
