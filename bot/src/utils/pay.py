"""Модуль для работы с YooMoney: создание платёжных ссылок и проверка оплат."""

import logging

from yoomoney import Quickpay, AsyncClient

from src.utils.config import settings

logger = logging.getLogger(__name__)


class YooMoneyProcessor:
    """Создание платёжных ссылок и проверка оплат через YooMoney API."""

    def __init__(self) -> None:
        self._client: AsyncClient | None = None
        self._receiver: str | None = None

    async def _get_client(self) -> AsyncClient:
        if self._client is None:
            self._client = AsyncClient(settings.YOOMONEY_TOKEN)
        return self._client

    async def _get_receiver(self) -> str:
        """Получить номер кошелька получателя (кэшируется)."""
        if self._receiver is None:
            client = await self._get_client()
            user = await client.account_info()
            self._receiver = user.account
        return self._receiver

    async def close(self) -> None:
        if self._client is not None:
            await self._client.__aexit__(None, None, None)
            self._client = None

    async def create_payment_link(self, label: str) -> str:
        """Создать Quickpay-ссылку для оплаты.

        Args:
            label: Уникальная метка платежа (используется для проверки оплаты).

        Returns:
            URL страницы оплаты.
        """
        receiver = await self._get_receiver()
        quickpay = Quickpay(
            receiver=receiver,
            quickpay_form="shop",
            targets="Доступ к закрытому каналу",
            paymentType="AC", # AC = выбор способа оплаты пользователем
            sum=settings.PAYMENT_PRICE_RUB,
            label=label,
        )
        return quickpay.base_url

    async def check_payment(self, label: str) -> bool:
        """Проверить, была ли оплачена операция с заданным label.

        Args:
            label: Метка платежа.

        Returns:
            True если найдена успешная операция с данной меткой.
        """
        try:
            client = await self._get_client()
            history = await client.operation_history(label=label)
            for op in history.operations:
                if op.label == label and op.status == "success":
                    return True
            return False
        except Exception as e:
            logger.error("Ошибка при проверке оплаты YooMoney (label=%s): %s", label, e)
            return False

    async def get_operation_history(self):
        """Получить историю операций без фильтрации.

        Returns:
            Объект истории операций из YooMoney API.
        """
        client = await self._get_client()
        # records=100 — явно указываем количество записей
        # operation_type="deposition" — входящие платежи (от пользователей)
        return await client.operation_history(records=100)

    async def __aenter__(self) -> "YooMoneyProcessor":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
