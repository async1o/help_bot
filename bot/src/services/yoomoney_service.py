"""Сервис оплаты доступа через YooMoney."""

import logging
import uuid

from src.db.repositories import PaymentRepository, UserRepository
from src.schemas.payments import PaymentSchema
from src.utils.config import settings
from src.utils.pay import YooMoneyProcessor

logger = logging.getLogger(__name__)


class YooMoneyService:
    """Работа с платежами YooMoney: генерация ссылки, проверка оплаты, активация."""

    def __init__(self) -> None:
        self._payment_repo = PaymentRepository()
        self._user_repo = UserRepository()
        self._processor = YooMoneyProcessor()

    async def generate_payment_link(self, user_id: int) -> str:
        """Сгенерировать уникальную платёжную ссылку YooMoney.

        Args:
            user_id: ID пользователя.

        Returns:
            URL страницы оплаты YooMoney.
        """
        label = f"user_{user_id}_{uuid.uuid4().hex[:12]}"
        link = await self._processor.create_payment_link(label)
        logger.info("YooMoney payment link generated: user=%s, label=%s", user_id, label)
        return link

    async def check_and_activate(self, user_id: int, label: str) -> bool:
        """Проверить оплату и активировать подписку.

        Args:
            user_id: ID пользователя.
            label: Метка платежа для проверки.

        Returns:
            True если оплата подтверждена и подписка активирована.
        """
        paid = await self._processor.check_payment(label)
        if not paid:
            return False

        # Записываем платёж (без telegram_payment_charge_id — используем label)
        await self._payment_repo.add_payment(PaymentSchema(
            user_id=str(user_id),
            telegram_payment_charge_id=f"yoomoney_{label}",
            amount=settings.PAYMENT_PRICE_RUB * 100,  # в копейках
            currency="RUB",
        ))

        # Активируем подписку
        await self._payment_repo.activate_user_subscription(str(user_id))
        logger.info("YooMoney payment confirmed and subscription activated: user=%s", user_id)
        return True

    async def close(self) -> None:
        """Закрыть соединение с YooMoney."""
        await self._processor.close()
