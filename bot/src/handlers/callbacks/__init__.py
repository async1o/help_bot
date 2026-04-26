__all__ = [
    "callbacks_router",
]

from aiogram import Router

from .operators import router as operator_router

callbacks_router = Router()

callbacks_router.include_routers(operator_router)
