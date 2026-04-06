"""Фильтр для проверки подписки пользователя на канал."""

import logging

from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram import Bot

from src.services.subscription_service import SubscriptionService
from src.utils.config import settings

logger = logging.getLogger(__name__)


class IsSubscribed(BaseFilter):
    """Проверяет, подписан ли пользователь на канал (если CHANNEL_ID настроен)."""

    async def __call__(self, message: Message, bot: Bot) -> bool:
        if not message.from_user:
            return False

        # Если канал не настроен — пропускаем всех
        if not settings.is_channel_set:
            return True

        service = SubscriptionService()
        return await service.is_user_allowed(bot, message.from_user.id)
