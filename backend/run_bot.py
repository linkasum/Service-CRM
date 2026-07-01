#!/usr/bin/env python3
"""
Скрипт запуска Telegram бота в polling режиме.
Запускается ОТДЕЛЬНО от FastAPI сервера.

Использование:
    cd backend
    source venv/bin/activate
    python run_bot.py
"""
import asyncio
import sys
import os

# Добавляем backend в path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import get_settings
from core.logging import logger

settings = get_settings()


async def main():
    """Запустить Telegram бота в polling режиме"""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не настроен. Добавьте его в .env файл.")
        sys.exit(1)

    logger.info("=" * 50)
    logger.info("Telegram бот запускается в polling режиме")
    logger.info(f"Бот: @{settings.TELEGRAM_BOT_TOKEN.split(':')[0]}")
    logger.info("=" * 50)

    # Импортируем бота (не запуская FastAPI)
    from bot.bot import dp, bot, stop_bot

    try:
        await dp.start_polling(bot, polling_timeout=20)
    except KeyboardInterrupt:
        logger.info("Остановка бота по Ctrl+C...")
    except Exception as e:
        logger.error(f"Критическая ошибка бота: {e}", exc_info=True)
    finally:
        await stop_bot()


if __name__ == "__main__":
    asyncio.run(main())
