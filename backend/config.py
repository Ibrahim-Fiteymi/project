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

    # --- Database ---
    database_url: Optional[str] = None

    # --- JWT / authentication ---
    # In production, jwt_secret MUST be set via env. In dev a stable per-machine
    # fallback is generated at process start so tokens survive reload but are
    # never the literal "change-me" placeholder.
    jwt_secret: Optional[str] = None
    jwt_alg: str = "HS256"
    # Legacy single TTL — kept for back-compat. New code uses the two below.
    jwt_ttl_seconds: int = 3600
    # Access tokens: short-lived, sent on every request.
    jwt_access_ttl_seconds: int = 900           # 15 minutes
    # Refresh tokens: long-lived, stored hashed in DB so they can be revoked.
    jwt_refresh_ttl_seconds: int = 60 * 60 * 24 * 30  # 30 days
    password_min_length: int = 8

    # --- Storage ---
    storage_root: str = str(ROOT / "backend" / "storage")

    # --- AI / inference ---
    model_checkpoint: str = str(ROOT / "outputs" / "checkpoints" / "best_model.pth")
    image_size: int = 256          # tied to the trained U-Net; not a user knob
    threshold: float = 0.7         # selected operating point (lowest counting MAE)
    min_area: int = 5              # noise-filter for connected-components counting

    # --- Upload limits ---
    max_upload_bytes: int = 50 * 1024 * 1024  # 50 MB

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
