"""Обработчики сообщений оператора в режиме диалога с пользователем."""

import logging

from aiogram import Router, F
from aiogram.types import Message

from src.filters.in_dialog import IsOperatorInDialog
from src.services.dialog_service import DialogService

router = Router()
router.message.filter(IsOperatorInDialog())

logger = logging.getLogger(__name__)

DIALOG_ENDED_OPERATOR = 'Диалог завершён.'
DIALOG_ENDED_USER = 'Оператор завершил диалог. Спасибо за обращение!'


@router.message(F.text == '/stop_dialog')
async def stop_dialog(message: Message):
    operator_id = str(message.from_user.id)
    sender_id = await DialogService.end_dialog(operator_id)
    if not sender_id:
        await message.answer('У вас нет активного диалога.')
        return

    await message.bot.send_message(chat_id=operator_id, text=DIALOG_ENDED_OPERATOR)
    await message.bot.send_message(chat_id=sender_id, text=DIALOG_ENDED_USER)


@router.message()
async def forward_operator_message_to_user(message: Message):
    """Пересылает сообщение оператора пользователю от имени бота."""
    operator_id = str(message.from_user.id)
    user_id = await DialogService.get_user_for_operator(operator_id)
    if not user_id:
        return

    try:
        await message.bot.copy_message(
            chat_id=user_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
    except Exception as e:
        logger.exception('Не удалось переслать сообщение оператора пользователю: %s', e)
        await message.answer('Не удалось отправить сообщение. Попробуйте текст или другой формат.')
