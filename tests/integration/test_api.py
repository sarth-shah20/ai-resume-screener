from fastapi.testclient import TestClient
from src.models.schemas import CandidateAnalysis, ExtractedJob
from app.main import app, provider

class FakeLLM:
    async def extract_job(self, text):
        return ExtractedJob.model_validate({"title": "Backend Engineer", "requirements": [{"id": "r1", "category": "must_have_skill", "description": "Python"}]})
    async def analyze_candidate(self, job, text):
        return CandidateAnalysis.model_validate({"summary": "Relevant backend experience", "requirement_matches": [{"requirement_id": "r1", "status": "demonstrated", "confidence": "high", "evidence": "Built Python APIs", "explanation": "Direct evidence"}]})
    async def verify_github(self, claim, evidence):
        return {"status": "inconclusive", "supported_claims": [], "unsupported_claims": [], "evidence": []}

app.dependency_overrides[provider] = lambda: FakeLLM()
client = TestClient(app)

def test_health():
    assert client.get("/health").status_code == 200

def test_analyze_pasted_text():
    response = client.post("/api/v1/analyze", data={"jd_text": "Need Python", "resume_text": "Built Python APIs", "blind_mode": "true"})
    assert response.status_code == 200
    assert response.json()["candidates"][0]["verified_score"] == 100
    assert response.json()["candidates"][0]["source_name"] == "Candidate 1"
    request_id = response.json()["request_id"]
    jobs = client.get("/api/v1/jobs")
    assert jobs.status_code == 200
    assert any(job["job_id"] == request_id for job in jobs.json()["jobs"])
    candidates = client.get(f"/api/v1/jobs/{request_id}/candidates")
    assert candidates.status_code == 200
    assert candidates.json()["candidates"][0]["candidate_id"] == "candidate-1"
    detail = client.get(f"/api/v1/jobs/{request_id}/candidates/candidate-1")
    assert detail.status_code == 200
    assert detail.json()["verified_score"] == 100

def test_rejects_missing_resume():
    assert client.post("/api/v1/analyze", data={"jd_text": "Need Python"}).status_code == 422
