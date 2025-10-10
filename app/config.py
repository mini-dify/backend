from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # OPENAI_API_KEY: str
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None

    LMS_API_BASE_URL: str = "https://digital.itanah.us/api/lms/v1"
    LMS_API_AUTH_HEADER: str = "Basic Z29jeXpob2Q6aGFuYXRpMTIz"

    class Config:
        env_file = ".env"


settings = Settings()
