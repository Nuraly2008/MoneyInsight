"""MoneyInsight bot launcher.

This file is intentionally small. Telegram handlers, keyboards and report
calculations are separated into modules to keep the project readable.
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import ensure_directories, settings
from .database import init_db
from .handlers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """Start the Telegram bot."""
    if not settings.bot_token:
        raise RuntimeError(
            "BOT_TOKEN is not set. Create a .env file from .env.example and add your token."
        )

    ensure_directories()
    init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    logger.info("MoneyInsight bot started")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
