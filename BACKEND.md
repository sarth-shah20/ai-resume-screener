# FastAPI Backend

## Start locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --reload
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

`POST /api/v1/analyze` accepts a job description and up to five resumes as text, PDF, DOCX, or TXT. `POST /api/v1/github/verify` performs optional, read-only verification of one canonical public GitHub repository URL.

Completed analyses are persisted to SQLite. Candidate evaluations run concurrently while `MAX_CONCURRENT_EVALUATIONS` bounds NVIDIA API usage.
