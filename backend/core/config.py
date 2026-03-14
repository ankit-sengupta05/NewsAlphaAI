"""
backend/core/config.py
Central configuration – reads from .env via pydantic-settings.
All paths & secrets live HERE; no raw os.getenv scattered across codebase.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]   # project root


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────
    llm_provider: Literal["gemma", "openai", "mistral", "llama"] = "gemma"
    gemma_model_path: Path = BASE_DIR / "models" / "LLM" / "Gemma-3-4B-IT"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # ── News APIs ─────────────────────────────────
    newsapi_key: str = ""
    gnews_api_key: str = ""
    alphavantage_key: str = ""

    # ── Stock Data ────────────────────────────────
    yahoo_finance_enabled: bool = True
    alphavantage_stock_key: str = ""

    # ── Vector Database ───────────────────────────
    vectordb_provider: Literal["chroma", "faiss"] = "chroma"
    chroma_persist_dir: Path = BASE_DIR / "data" / "embeddings" / "chroma"
    faiss_index_dir: Path = BASE_DIR / "data" / "embeddings" / "faiss"

    # ── Data Storage ──────────────────────────────
    news_data_dir: Path = BASE_DIR / "data" / "news"
    stock_data_dir: Path = BASE_DIR / "data" / "stocks"
    memory_dir: Path = BASE_DIR / "data" / "memory"     # agent memory – separate!

    # ── LangSmith ─────────────────────────────────
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "NewsAlphaAI"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    # ── ML / RL ──────────────────────────────────
    ml_model_dir: Path = BASE_DIR / "data" / "ml_models"
    rl_feedback_log: Path = BASE_DIR / "data" / "rl" / "feedback.jsonl"
    rl_reward_threshold: float = 0.6

    # ── Embedding ─────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── Server ────────────────────────────────────
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    def ensure_dirs(self):
        """Create all necessary data directories."""
        dirs = [
            self.news_data_dir,
            self.stock_data_dir,
            self.memory_dir,
            self.chroma_persist_dir,
            self.faiss_index_dir,
            self.ml_model_dir,
            self.rl_feedback_log.parent,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()

# ── Propagate LangSmith env vars (langchain reads them from env) ──────────────
if settings.langchain_tracing_v2:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
