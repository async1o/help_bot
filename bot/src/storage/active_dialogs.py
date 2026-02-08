"""Хранилище активных диалогов оператор <-> пользователь (один пользователь — один диалог)."""

from typing import Optional

# operator_id -> sender_id (user_id)
_active_dialogs: dict[str, str] = {}


def add_dialog(operator_id: str, sender_id: str) -> None:
    """Начать диалог. Если пользователь уже в диалоге — старый диалог завершается."""
    remove_dialog_by_user(str(sender_id))
    _active_dialogs[str(operator_id)] = str(sender_id)


def remove_dialog_by_user(sender_id: str) -> Optional[str]:
    """Удалить диалог по пользователю. Возвращает operator_id или None."""
    sid = str(sender_id)
    for op_id, user_id in list(_active_dialogs.items()):
        if user_id == sid:
            del _active_dialogs[op_id]
            return op_id
    return None


def remove_dialog_by_operator(operator_id: str) -> Optional[str]:
    return _active_dialogs.pop(str(operator_id), None)


def get_user_by_operator(operator_id: str) -> Optional[str]:
    return _active_dialogs.get(str(operator_id))


def get_operator_by_user(sender_id: str) -> Optional[str]:
    for op_id, user_id in _active_dialogs.items():
        if user_id == str(sender_id):
            return op_id
    return None


def is_operator_in_dialog(operator_id: str) -> bool:
    return str(operator_id) in _active_dialogs


def is_user_in_dialog(sender_id: str) -> bool:
    return get_operator_by_user(sender_id) is not None
