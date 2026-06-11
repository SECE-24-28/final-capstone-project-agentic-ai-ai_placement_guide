from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    APP_NAME: str = "AI Placement Preparation Agent"
    APP_DEBUG: bool = False

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "placement_ai"

    SECRET_KEY: str = "change-me-in-production-use-32-char-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
