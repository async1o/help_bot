"""Фильтры для проверки участия в активном диалоге."""

from aiogram.filters import BaseFilter
from aiogram.types import Message

from src.services.dialog_service import DialogService


class IsOperatorInDialog(BaseFilter):
    """Сообщение от оператора, у которого есть активный диалог."""

    async def __call__(self, message: Message) -> bool:
        return message.from_user and DialogService.is_operator_in_dialog(str(message.from_user.id))


class IsUserInDialog(BaseFilter):
    """Сообщение от пользователя, у которого есть активный диалог с оператором."""

    async def __call__(self, message: Message) -> bool:
        return message.from_user and DialogService.is_user_in_dialog(str(message.from_user.id))
