"""Сервис обращений: рассылка операторам, принятие обращения, старт диалога."""

import asyncio
import logging
import uuid

from aiogram import Bot

from src.db.repositories import AdminRepository, MsgRepository
from src.schemas.messages import MsgSchema
from src.services.dialog_service import DialogService
from src.keyboards.sos import operator_request_kb

logger = logging.getLogger(__name__)


class SupportService:
    """Работа с обращениями и диалогами: параллельная рассылка, уникальный request_id."""

    def __init__(self):
        self._msg_repo = MsgRepository()
        self._admin_repo = AdminRepository()

    async def notify_operators(self, bot: Bot, request_text: str, sender_id: int) -> str | None:
        """
        Разослать обращение всем операторам. Возвращает request_id при успехе, None если операторов нет.
        Сообщения отправляются параллельно.
        """
        operators = await self._admin_repo.get_all_operators()
        if not operators:
            return None

        request_id = str(uuid.uuid4())
        text = f'Новый запрос:\n{request_text}'
        keyboard = operator_request_kb(request_id)

        async def send_one(operator_id: str):
            msg = await bot.send_message(
                chat_id=operator_id,
                text=text,
                reply_markup=keyboard
            )
            await self._msg_repo.add_message(MsgSchema(
                request_id=request_id,
                message_id=msg.message_id,
                operator_id=operator_id,
                sender_id=str(sender_id)
            ))

        await asyncio.gather(*[send_one(op[0]) for op in operators])
        return request_id

    async def accept_request(self, bot: Bot, request_id: str, operator_id: str) -> str | None:
        """
        Оператор принимает обращение: удалить сообщения у всех операторов, начать диалог.
        Возвращает sender_id при успехе, None если обращение уже принято.
        """
        rows = await self._msg_repo.get_by_request_id(request_id)
        if not rows:
            return None

        sender_id = str(rows[0].sender_id)

        async def delete_one(row):
            try:
                await bot.delete_message(chat_id=row.operator_id, message_id=row.message_id)
            except Exception as e:
                logger.debug('Delete message %s: %s', row.message_id, e)

        await asyncio.gather(*[delete_one(r) for r in rows])
        await self._msg_repo.delete_by_request_id(request_id)

        await DialogService.start_dialog(operator_id=operator_id, sender_id=sender_id)
        return sender_id
