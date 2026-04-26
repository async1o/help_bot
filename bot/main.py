import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties

from src.utils.config import settings
from src.handlers import main_router
from src.db.db import create_tables_if_not_exists

logging.basicConfig(level=logging.INFO)

# Отключаем логирование httpx-запросов
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def main():

    session = AiohttpSession()

    bot = Bot(
        token=settings.TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    dp = Dispatcher()
    dp.include_router(main_router)

    # Авто-создание таблиц если не существуют
    await create_tables_if_not_exists()

    # Удаляем webhook (если был установлен ранее), используем polling
    await bot.delete_webhook()
    logger.info("Webhook deleted (polling mode)")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("Polling error: %s", e)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
