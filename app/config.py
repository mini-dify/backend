from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    QDRANT_URL: str = "http://localhost:6334"
    QDRANT_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
