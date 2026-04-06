"""Сервис оплаты доступа к Telegram-каналу."""

import logging

from aiogram import Bot
from aiogram.types import LabeledPrice

from src.db.repositories import PaymentRepository, UserRepository
from src.schemas.payments import PaymentSchema
from src.utils.config import settings

logger = logging.getLogger(__name__)


class PaymentService:
    """Работа с платежами: отправка invoice, обработка успешной оплаты."""

    def __init__(self):
        self._payment_repo = PaymentRepository()
        self._user_repo = UserRepository()

    async def send_invoice(self, bot: Bot, user_id: int) -> None:
        """Отправить счёт на оплату."""
        if not settings.PAYMENT_TOKEN:
            raise ValueError(
                'PAYMENT_TOKEN не установлен. '
                'Получите его: @BotFather → Your Bot → Payments → Connect'
            )

        price = LabeledPrice(
            label='Доступ к каналу (навсегда)',
            amount=settings.PAYMENT_PRICE_RUB * 100  # в копейках
        )

        logger.info('Sending invoice: user=%s, amount=%s, provider_token=%s...',
                     user_id, settings.PAYMENT_PRICE_RUB, settings.PAYMENT_TOKEN[:10])

        await bot.send_invoice(
            chat_id=user_id,
            provider_token=settings.PAYMENT_TOKEN,
            title='Доступ к каналу',
            description='Одноразовая оплата за бессрочный доступ к закрытому Telegram-каналу',
            payload=f'user_{user_id}_access',
            currency='RUB',
            prices=[price],
        )
        logger.info('Invoice sent successfully: user=%s', user_id)

    async def process_successful_payment(self, user_id: int, charge_id: str, total_amount: int) -> None:
        """Обработать успешную оплату."""
        logger.info('process_successful_payment START: user=%s, charge=%s, amount=%s',
                     user_id, charge_id, total_amount)
        try:
            # Записываем платёж
            await self._payment_repo.add_payment(PaymentSchema(
                user_id=str(user_id),
                telegram_payment_charge_id=charge_id,
                amount=total_amount,
                currency='RUB',
            ))
            logger.info('Payment recorded: user=%s, charge=%s', user_id, charge_id)
        except Exception as e:
            logger.warning('Failed to record payment (may be duplicate): user=%s, error=%s', user_id, e)

        # Активируем подписку (это безопасно при повторных вызовах)
        try:
            logger.info('Activating subscription for user=%s', user_id)
            await self._payment_repo.activate_user_subscription(str(user_id))
            logger.info('Subscription activated for user=%s', user_id)
        except Exception as e:
            logger.error('Failed to activate subscription for user=%s: %s', user_id, e)
            raise
