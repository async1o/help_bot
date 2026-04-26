"""Сервис активных диалогов: один пользователь — один диалог с одним оператором (персистентный)."""

from typing import Optional

from src.db.repositories import DialogRepository
from src.schemas.dialogs import DialogSchema


class DialogService:
    """Единая точка работы с активными диалогами (хранение в БД)."""

    @staticmethod
    async def start_dialog(operator_id: str, sender_id: str) -> None:
        """Начать диалог. Если пользователь или оператор уже в другом диалоге — тот завершается."""
        repo = DialogRepository()
        await repo.add_dialog(
            DialogSchema(operator_id=operator_id, sender_id=sender_id)
        )

    @staticmethod
    async def end_dialog(operator_id: str) -> Optional[str]:
        """Завершить диалог оператора. Возвращает sender_id или None."""
        repo = DialogRepository()
        return await repo.remove_by_operator(operator_id)

    @staticmethod
    async def get_user_for_operator(operator_id: str) -> Optional[str]:
        """ID пользователя, с которым общается оператор, или None."""
        repo = DialogRepository()
        return await repo.get_user_by_operator(operator_id)

    @staticmethod
    async def get_operator_for_user(sender_id: str) -> Optional[str]:
        """ID оператора, с которым общается пользователь, или None."""
        repo = DialogRepository()
        return await repo.get_operator_by_user(sender_id)

    @staticmethod
    async def is_operator_in_dialog(operator_id: str) -> bool:
        repo = DialogRepository()
        return await repo.is_operator_in_dialog(operator_id)

    @staticmethod
    async def is_user_in_dialog(sender_id: str) -> bool:
        repo = DialogRepository()
        return await repo.is_user_in_dialog(sender_id)
