from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    QDRANT_URL: str = "http://minidify_qdrant:6333"
    QDRANT_API_KEY: Optional[str] = None
    HTTP_BASIC_USERNAME: str = "admin"
    HTTP_BASIC_PASSWORD: str = "admin"

    LMS_API_AUTHORIZATION: str = "Basic Z29jeXpob2Q6aGFuYXRpMTIz"

    EMBEDDING_API_URL: str = "https://digital.itanah.us/api/lms/v1/embeddings"
    EMBEDDING_MODEL: str = "qwen/qwen2.5-embedding-32b"

    CHAT_COMPLETIONS_API_URL: str = "https://digital.itanah.us/api/lms/v1/chat/completions"
    CHAT_MODEL: str = "qwen/qwen2.5-coder-32b"

    class Config:
        env_file = ".env"

settings = Settings()
