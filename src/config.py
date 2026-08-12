from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    llm_provider: str = "nvidia"
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "openai/gpt-oss-120b"
    github_token: str = ""
    database_url: str = "sqlite:///data/resume_screener.db"
    max_file_size_mb: int = Field(default=5, ge=1, le=20)
    max_resumes_per_request: int = Field(default=5, ge=1, le=10)
    max_concurrent_evaluations: int = Field(default=3, ge=1, le=10)
    llm_timeout_seconds: int = Field(default=90, ge=10, le=180)

@lru_cache
def get_settings() -> Settings:
    return Settings()
