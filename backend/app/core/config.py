from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Banana Storage Saver"
    cors_origins: list[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://food-spoilage-detection-livid.vercel.app",
]
    artifacts_dir: Path = REPO_ROOT / "ml" / "artifacts"
    references_dir: Path = REPO_ROOT / "data" / "references"
    log_level: str = "INFO"
    prefer_lstm: bool = True
    model_version: str = "0.1.0"

    model_config = SettingsConfigDict(env_prefix="BSS_", env_file=".env", extra="ignore")


settings = Settings()
