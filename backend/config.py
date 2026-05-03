"""Application settings, loaded from environment variables and .env file.

Phase 1 step 1 — foundation only:
- Loads safe-default values so the app runs without an .env (matches today's MVP).
- Adds env-driven knobs for CORS, storage paths, AI thresholds, and upload size.
- Includes (optional) database_url and jwt_secret fields for later phases; both
  are None by default so the absence of a DB does not break the current MVP.

Anything that has not been wired yet (auth, DB) reads its setting but is not
yet used at runtime. Phase 1 step 2+ will plug them in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Environment ---
    env: str = Field(default="dev", description='dev | staging | prod')

    # --- CORS ---
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    # --- Database (Phase 1 step 2+; unused today) ---
    database_url: Optional[str] = None

    # --- JWT (Phase 1 step 3+; unused today) ---
    jwt_secret: Optional[str] = None
    jwt_alg: str = "HS256"
    jwt_ttl_seconds: int = 3600

    # --- Storage ---
    storage_root: str = str(ROOT / "backend" / "storage")

    # --- AI / inference ---
    model_checkpoint: str = str(ROOT / "outputs" / "checkpoints" / "best_model.pth")
    image_size: int = 256          # tied to the trained U-Net; not a user knob
    threshold: float = 0.8         # corrected operating point (batch_count_refined)
    min_area: int = 1

    # --- Upload limits ---
    max_upload_bytes: int = 25 * 1024 * 1024  # 25 MB

    # --- Rate limits (Phase 2; unused today) ---
    rate_limit_login_per_minute: int = 10
    rate_limit_upload_per_minute: int = 30
    rate_limit_reports_per_minute: int = 60

    # --- Derived helpers ---
    @property
    def upload_dir(self) -> Path:
        return Path(self.storage_root) / "uploads"

    @property
    def result_dir(self) -> Path:
        return Path(self.storage_root) / "results"

    @property
    def checkpoint_path(self) -> Path:
        p = Path(self.model_checkpoint)
        return p if p.is_absolute() else (ROOT / p)


settings = Settings()
