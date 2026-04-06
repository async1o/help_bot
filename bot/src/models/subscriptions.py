"""SQLAlchemy-модель для отслеживания подписок пользователей на канал."""

from datetime import datetime
from typing import Union

from sqlalchemy.orm import Mapped, mapped_column

from src.db.db import Base


class SubscriptionModel(Base):
    __tablename__ = 'subscriptions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(unique=True, index=True)
    is_subscribed: Mapped[bool] = mapped_column(default=False)
    """Статус подписки: True — пользователь в канале, False — вышел"""
    subscribed_at: Mapped[Union[datetime, None]] = mapped_column(default=None)
    """Дата последней подписки (входа в канал)"""
    unsubscribed_at: Mapped[Union[datetime, None]] = mapped_column(default=None)
    """Дата отписки (выхода из канала)"""
    last_checked_at: Mapped[Union[datetime, None]] = mapped_column(default=None)
    """Дата последней проверки статуса через API"""
