from typing import Annotated
import httpx
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from src.config import Settings, get_settings
from src.models.schemas import AnalyzeResponse, GitHubVerifyRequest, GitHubVerifyResponse
from src.parsers import DocumentParseError, parse_document
from src.services.github_service import GitHubVerifier
from src.services.llm_service import LLMError, NvidiaLLMProvider
from src.services.screening_service import ScreeningService

app = FastAPI(title="AI Resume Screening API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"], allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])

def provider(settings: Settings = Depends(get_settings)) -> NvidiaLLMProvider:
    try:
        return NvidiaLLMProvider(settings)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@app.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"status": "ok", "llm_provider": settings.llm_provider, "model": settings.nvidia_model}

@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze(jd_text: Annotated[str | None, Form()] = None, jd_file: Annotated[UploadFile | None, File()] = None, resume_text: Annotated[str | None, Form()] = None, resume_files: Annotated[list[UploadFile] | None, File()] = None, blind_mode: Annotated[bool, Form()] = True, settings: Settings = Depends(get_settings), llm: NvidiaLLMProvider = Depends(provider)) -> AnalyzeResponse:
    if bool(jd_text and jd_text.strip()) == bool(jd_file):
        raise HTTPException(422, "Provide exactly one of jd_text or jd_file.")
    files = resume_files or []
    count = (1 if resume_text and resume_text.strip() else 0) + len(files)
    if count == 0 or count > settings.max_resumes_per_request:
        raise HTTPException(422, f"Provide between 1 and {settings.max_resumes_per_request} resumes.")
    try:
        limit = settings.max_file_size_mb * 1024 * 1024
        job = jd_text.strip() if jd_text else parse_document(jd_file.filename or "job", await jd_file.read(), limit)
        resumes = []
        if resume_text and resume_text.strip():
            resumes.append(("Pasted resume", resume_text.strip()))
        for file in files:
            resumes.append((file.filename or "Uploaded resume", parse_document(file.filename or "resume", await file.read(), limit)))
        return await ScreeningService(llm).analyze(job, resumes, blind_mode)
    except DocumentParseError as exc:
        raise HTTPException(422, str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(502, str(exc)) from exc

@app.post("/api/v1/github/verify", response_model=GitHubVerifyResponse)
async def verify_github(request: GitHubVerifyRequest, settings: Settings = Depends(get_settings), llm: NvidiaLLMProvider = Depends(provider)) -> GitHubVerifyResponse:
    try:
        return await GitHubVerifier(settings, llm).verify(request.repository_url, request.claimed_description)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except (httpx.HTTPError, LLMError) as exc:
        raise HTTPException(502, "GitHub verification is temporarily unavailable.") from exc
