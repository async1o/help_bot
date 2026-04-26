__all__ = [
    "main_router",
]

from aiogram import Router

from .message import messages_router
from .callbacks import callbacks_router

main_router = Router()

main_router.include_routers(messages_router, callbacks_router)
