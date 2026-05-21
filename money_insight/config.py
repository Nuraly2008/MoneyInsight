"""Application configuration for MoneyInsight.

Secrets are intentionally loaded from environment variables instead of being
hardcoded in source code. This makes the bot safer and easier to deploy.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")
TEMP_DIR = BASE_DIR / os.getenv("TEMP_DIR", "temp")
CHARTS_DIR = BASE_DIR / os.getenv("CHARTS_DIR", "charts")


@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "").strip()
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    openrouter_base_url: str = os.getenv(
        "OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1",
    ).strip()
    ai_model: str = os.getenv(
        "AI_MODEL",
        "deepseek/deepseek-chat-v3-0324:free",
    ).strip()
    database_path: Path = DATA_DIR / os.getenv("DATABASE_NAME", "money_insight.db")
    merchants_file: Path = DATA_DIR / os.getenv("MERCHANTS_FILE", "merchants.json")
    max_transactions_preview: int = int(os.getenv("MAX_TRANSACTIONS_PREVIEW", "10"))


settings = Settings()

# Compatibility with the original code style: `from config import BOT_TOKEN`.
BOT_TOKEN = settings.bot_token


def ensure_directories() -> None:
    """Create runtime directories used by the bot."""
    for path in (DATA_DIR, TEMP_DIR, CHARTS_DIR):
        path.mkdir(parents=True, exist_ok=True)
