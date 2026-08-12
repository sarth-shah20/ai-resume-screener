import re
from urllib.parse import urlparse
import httpx
from src.config import Settings
from src.models.schemas import GitHubVerifyResponse
from src.services.llm_service import LLMProvider

MANIFESTS = {"readme.md", "requirements.txt", "pyproject.toml", "package.json", "pom.xml", "go.mod", "dockerfile"}

class GitHubVerifier:
    def __init__(self, settings: Settings, llm: LLMProvider):
        self.settings, self.llm = settings, llm

    async def verify(self, url: str, claim: str) -> GitHubVerifyResponse:
        owner, repo = canonical_repository(url)
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"
        async with httpx.AsyncClient(base_url="https://api.github.com", headers=headers, timeout=15, follow_redirects=False) as client:
            meta_response = await client.get(f"/repos/{owner}/{repo}")
            if meta_response.status_code == 404:
                return unavailable(url, "Repository is unavailable or not public.")
            if meta_response.status_code in {403, 429}:
                return unavailable(url, "GitHub API rate limit reached.")
            meta_response.raise_for_status()
            meta = meta_response.json()
            root_response = await client.get(f"/repos/{owner}/{repo}/contents")
            root_response.raise_for_status()
            entries = root_response.json()
            files: dict[str, str] = {}
            for entry in entries:
                if entry.get("type") == "file" and entry.get("name", "").lower() in MANIFESTS and len(files) < 5:
                    raw = await client.get(entry["url"], headers={**headers, "Accept": "application/vnd.github.raw+json"})
                    if raw.is_success and len(raw.content) <= 100_000:
                        files[entry["name"]] = raw.text[:20_000]
        facts = {"name": meta["name"], "description": meta.get("description"), "primary_language": meta.get("language"), "last_updated": meta.get("updated_at"), "files": files}
        assessment = await self.llm.verify_github(claim, facts)
        return GitHubVerifyResponse(**assessment, repository={k: v for k, v in facts.items() if k != "files"}, limitations=["Public repository evidence cannot prove candidate authorship.", "Only metadata and selected root files were inspected."])

def canonical_repository(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"} or parsed.query or parsed.fragment:
        raise ValueError("Only canonical public HTTPS GitHub repository URLs are supported.")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) != 2 or not all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) for p in parts):
        raise ValueError("The URL must have the form https://github.com/owner/repository.")
    return parts[0], parts[1].removesuffix(".git")

def unavailable(url: str, reason: str) -> GitHubVerifyResponse:
    return GitHubVerifyResponse(status="unavailable", repository={"url": url}, supported_claims=[], unsupported_claims=[], evidence=[], limitations=[reason])
