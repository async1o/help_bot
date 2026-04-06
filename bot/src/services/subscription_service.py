"""Сервис для проверки и управления подпиской пользователя на канал."""

import logging
from datetime import datetime
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError
from aiogram.enums import ChatMemberStatus

from src.db.repositories import SubscriptionRepository
from src.utils.config import settings

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Проверка статуса подписки пользователя на канал через Telegram API."""

    def __init__(self) -> None:
        self._repo = SubscriptionRepository()

    async def check_user_subscription(self, bot: Bot, user_id: int) -> bool:
        """Проверить, подписан ли пользователь на канал через Telegram API.

        Обновляет статус в БД. Возвращает True если пользователь подписан.
        """
        if not settings.is_channel_set:
            logger.warning('CHANNEL_ID не настроен, проверка подписки пропущена')
            return True  # Если канал не настроен — пропускаем проверку

        try:
            member = await bot.get_chat_member(
                chat_id=settings.CHANNEL_ID,
                user_id=user_id,
            )

            is_subscribed = member.status in (
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR,
                "join_request",
            )

            # Обновляем в БД
            if is_subscribed:
                await self._repo.mark_subscribed(str(user_id))
            else:
                await self._repo.mark_unsubscribed(str(user_id))

            return is_subscribed

        except TelegramForbiddenError:
            # Бот заблокирован каналом или пользователь скрыл профиль
            logger.warning(
                'TelegramForbiddenError при проверке подписки user=%s', user_id
            )
            await self._repo.mark_unsubscribed(str(user_id))
            return False

        except TelegramAPIError as e:
            logger.error('Ошибка при проверке подписки user=%s: %s', user_id, e)
            # Возвращаем последнее известное значение из БД
            return await self._repo.is_user_subscribed(str(user_id))

    async def is_user_allowed(self, bot: Bot, user_id: int) -> bool:
        """Проверить, разрешено ли пользователю использовать бота.

        Пользователь допускается если:
        - Он уже когда-либо оплачивал (has_paid_ever=True), И
        - Он подписан на канал
        """
        from src.db.repositories import UserRepository

        user = await UserRepository().get_user_by_id(str(user_id))

        # Если пользователь ни разу не оплачивал — разрешаем использование
        if user is None or not user.has_paid_ever:
            return True

        # Если оплачивал — проверяем подписку на канал
        is_subscribed = await self.check_user_subscription(bot, user_id)

        if not is_subscribed:
            logger.info(
                'Пользователь %s выходил из канала, доступ заблокирован до возвращения',
                user_id,
            )

        return is_subscribed

    async def on_user_returned(self, bot: Bot, user_id: int) -> bool:
        """Пользователь вернулся в канал — восстановить доступ.

        Вызывается при обнаружении что пользователь снова в канале.
        Возвращает True если доступ восстановлен.
        """
        from src.db.repositories import UserRepository

        user = await UserRepository().get_user_by_id(str(user_id))
        if user is None or not user.has_paid_ever:
            return False

        # Проверяем через API
        is_subscribed = await self.check_user_subscription(bot, user_id)

        if is_subscribed and user.is_paid is False:
            # Восстанавливаем доступ
            from src.db.repositories import PaymentRepository

            await PaymentRepository().activate_user_subscription(str(user_id))
            logger.info('Доступ восстановлен для пользователя %s', user_id)
            return True

        return is_subscribed

    async def get_invite_link(self) -> Optional[str]:
        """Получить ссылку для вступления в канал из конфига."""
        if settings.CHANNEL_INVITE_LINK:
            return settings.CHANNEL_INVITE_LINK
        logger.warning('CHANNEL_INVITE_LINK не настроен')
        return None
