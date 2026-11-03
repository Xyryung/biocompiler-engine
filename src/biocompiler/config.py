"""Validated runtime configuration. Secrets never appear in API responses."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    biocompiler_provider: Literal["mock", "meta"] = "mock"
    biocompiler_simulator: Literal["local", "modal"] = "local"
    meta_api_key: SecretStr = SecretStr("")
    model_api_key: SecretStr = SecretStr("")
    meta_base_url: str = "https://api.meta.ai/v1"
    meta_model: str = "muse-spark-1.3"
    meta_sam_model: str = "sam-3.1"
    protein_endpoint: str = ""
    protein_api_key: SecretStr = SecretStr("")
    protein_cost_usd: float | None = Field(default=None, ge=0)
    log_level: str = "INFO"
    simulation_timeout_seconds: int = Field(default=30, ge=1, le=120)


@lru_cache
def get_settings() -> Settings:
    return Settings()
