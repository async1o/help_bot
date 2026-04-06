from typing import Union
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from src.db.db import Base
from src.schemas.users import UserSchema

class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(unique=True)
    full_name: Mapped[Union[str, None]] = mapped_column(default=None)
    is_operator: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool]  = mapped_column(default=False)
    is_paid: Mapped[bool] = mapped_column(default=False)
    """Активна ли сейчас подписка (в канале ли пользователь)"""
    paid_at: Mapped[Union[datetime, None]] = mapped_column(default=None)
    """Дата последней активации подписки"""
    has_paid_ever: Mapped[bool] = mapped_column(default=False)
    """Оплачивал ли пользователь когда-либо (навсегда)"""
