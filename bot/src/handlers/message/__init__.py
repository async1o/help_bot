__all__ = [
    "messages_router",
]

from aiogram import Router

from .users import router as users_router
from .operators_dialog import router as operators_dialog_router
from .admin import router as admin_router

messages_router = Router()

# Сначала диалоги операторов (сообщения в активном диалоге), затем пользователи и админка
messages_router.include_routers(operators_dialog_router, users_router, admin_router)
