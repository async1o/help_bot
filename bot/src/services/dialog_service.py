"""Сервис активных диалогов: один пользователь — один диалог с одним оператором."""

from typing import Optional

from src.storage import active_dialogs


class DialogService:
    """Единая точка работы с активными диалогами (поддержка нескольких пользователей одновременно)."""

    @staticmethod
    def start_dialog(operator_id: str, sender_id: str) -> None:
        """Начать диалог. Если пользователь уже в другом диалоге — тот завершается."""
        active_dialogs.add_dialog(operator_id=operator_id, sender_id=sender_id)

    @staticmethod
    def end_dialog(operator_id: str) -> Optional[str]:
        """Завершить диалог оператора. Возвращает sender_id или None."""
        return active_dialogs.remove_dialog_by_operator(operator_id)

    @staticmethod
    def get_user_for_operator(operator_id: str) -> Optional[str]:
        """ID пользователя, с которым общается оператор, или None."""
        return active_dialogs.get_user_by_operator(operator_id)

    @staticmethod
    def get_operator_for_user(sender_id: str) -> Optional[str]:
        """ID оператора, с которым общается пользователь, или None."""
        return active_dialogs.get_operator_by_user(sender_id)

    @staticmethod
    def is_operator_in_dialog(operator_id: str) -> bool:
        return active_dialogs.is_operator_in_dialog(operator_id)

    @staticmethod
    def is_user_in_dialog(sender_id: str) -> bool:
        return active_dialogs.is_user_in_dialog(sender_id)
