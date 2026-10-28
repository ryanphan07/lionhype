import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")

    LLM_BASE_URL: str = "http://127.0.0.1:8080/v1"
    LLM_API_KEY: str = "local-key"
    LLM_MODEL: str = "qwen-coder"
    LLM_ENABLED: bool = True
    LLM_TIMEOUT: float = 30.0
    LLM_MAX_RETRIES: int = 2

    TTS_PROVIDER: str = "edge_tts"
    TTS_VOICE: str = "en-US-AnaNeural"
    TTS_ENABLED: bool = True
    TTS_TIMEOUT: float = 10.0
    TTS_MAX_RETRIES: int = 2

    LOG_LEVEL: str = "INFO"

    JOB_TTL_SECONDS: int = 3600
    CLEANUP_INTERVAL_SECONDS: int = 600
    MAX_VIDEO_SECONDS: float = 90.0
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    PUBLIC_BASE_URL: str = "http://localhost:8000"
    UPLOAD_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))


settings = Settings()
