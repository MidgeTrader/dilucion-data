"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    polygon_api_key: str = Field(default="", alias="POLYGON_API_KEY")
    massive_api_key: str = Field(default="", alias="MASSIVE_API_KEY")
    finnhub_api_key: str = Field(default="", alias="FINNHUB_API_KEY")
    benzinga_api_key: str = Field(default="", alias="BENZINGA_API_KEY")
    eodhd_api_key: str = Field(default="", alias="EODHD_API_KEY")
    stocksera_api_key: str = Field(default="", alias="STOCKSERA_API_KEY")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_admin_chat_id: int = Field(default=0, alias="TELEGRAM_ADMIN_CHAT_ID")

    sec_user_agent: str = Field(
        default="SecDilutionTracker user@example.com",
        alias="SEC_USER_AGENT",
    )

    data_dir: Path = Field(default=Path("../data"), alias="DATA_DIR")
    chroma_dir: Path = Field(default=Path("../data/chroma"), alias="CHROMA_DIR")

    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")

    chunk_size: int = 1500
    chunk_overlap: int = 200
    retriever_k: int = 5
    llm_temperature: float = 0.0
    deepseek_model: str = "deepseek-chat"
    deepseek_reasoning_model: str = "deepseek-reasoner"
    embedding_model: str = "text-embedding-3-small"

    sec_rate_limit_per_min: int = 10
    sec_rate_limit_per_sec: int = 10
    polygon_rate_limit_per_min: int = 5
    finnhub_rate_limit_per_min: int = 30
    rss_poll_interval_seconds: int = 120

    polygon_cache_ttl_hours: int = 24
    finnhub_cache_ttl_minutes: int = 5
    stocksera_cache_ttl_hours: int = 6

    @field_validator("data_dir", "chroma_dir", mode="before")
    @classmethod
    def resolve_path(cls, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            base = Path(__file__).resolve().parent
            path = (base / path).resolve()
        return path

    def ensure_directories(self) -> None:
        """Create required data directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)

    def validate_rag_keys(self) -> None:
        """Ensure keys required for RAG are present."""
        if not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required for RAG operations.")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for embeddings.")

    @property
    def companies_parquet(self) -> Path:
        return self.data_dir / "companies.parquet"

    @property
    def filings_parquet(self) -> Path:
        return self.data_dir / "filings_dilution.parquet"

    @property
    def cache_db_path(self) -> Path:
        return self.data_dir / "api_cache.sqlite"

    @property
    def sqlite_db_path(self) -> Path:
        return self.data_dir / "dilution.db"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    settings = Settings()
    settings.ensure_directories()
    return settings
