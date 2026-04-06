__all__ = ['callbacks_router',]

from aiogram import Router

from .operators import router as operator_router
from .payments import router as payment_router
from .yoomoney import router as yoomoney_router

callbacks_router = Router()

callbacks_router.include_routers(operator_router, payment_router, yoomoney_router)