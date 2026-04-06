"""Тестовый скрипт для проверки приглашения в закрытый канал.

По команде /invite_channel бот присылает сообщение с кнопкой,
нажав на которую пользователю предлагается подать заявку на вступление в канал.

Использование:
    cd bot
    python test_channel_invite.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from src.utils.config import settings
from src.services.subscription_service import SubscriptionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

_sub_service = SubscriptionService()


def channel_invite_kb(invite_link: str) -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой для вступления в закрытый канал."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подать заявку на вступление", url=invite_link)],
        ]
    )


async def cmd_invite_channel(message: Message, bot: Bot) -> None:
    """Обработчик команды /invite_channel."""
    invite_link = await _sub_service.get_invite_link()

    if invite_link is None:
        await message.answer(
            "❌ Не удалось получить ссылку для приглашения.\n\n"
            "Убедитесь, что в .env указан CHANNEL_INVITE_LINK "
            "(постоянная ссылка на канал вида https://t.me/+xxxxxxxxxx) "
            "или CHANNEL_ID, и бот является администратором канала."
        )
        return

    logger.info("Ссылка-приглашение: %s", invite_link)

    await message.answer(
        text=(
            "🔒 <b>Закрытый канал</b>\n\n"
            "Нажмите кнопку ниже, чтобы подать заявку на вступление. "
            "Администратор канала рассмотрит вашу заявку и одобрит её."
        ),
        reply_markup=channel_invite_kb(invite_link),
        parse_mode="HTML",
    )


async def main() -> None:
    """Запуск бота для тестирования приглашения в канал."""
    if not settings.is_channel_set:
        logger.error("CHANNEL_ID не указан в .env. Без него тест невозможен.")
        return

    bot = Bot(token=settings.TOKEN)
    dp = Dispatcher()

    dp.message.register(cmd_invite_channel, Command("invite_channel"))

    logger.info("Бот запущен. Отправьте команду /invite_channel для теста.")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
