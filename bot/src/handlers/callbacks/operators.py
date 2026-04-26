"""Принятие обращения оператором."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.services.support_service import SupportService

router = Router()
_support = SupportService()

DIALOG_STARTED_OPERATOR = (
    "Диалог начат с пользователем. Все ваши сообщения будут пересланы ему. "
    "Для завершения диалога введите /stop_dialog"
)
DIALOG_STARTED_USER = "С вами связался оператор. Опишите вашу проблему."


@router.callback_query(F.data.startswith("accept:"))
async def accept_request(callback: CallbackQuery):
    request_id = callback.data[7:].strip()
    if not request_id or len(request_id) > 64:
        await callback.answer("Ошибка данных.")
        return

    operator_id = str(callback.from_user.id)
    sender_id = await _support.accept_request(callback.bot, request_id, operator_id)

    if sender_id is None:
        await callback.answer("Обращение уже принято другим оператором.")
        return

    await callback.bot.send_message(chat_id=operator_id, text=DIALOG_STARTED_OPERATOR)
    await callback.bot.send_message(chat_id=sender_id, text=DIALOG_STARTED_USER)
    await callback.answer("Вы приняли обращение.")
