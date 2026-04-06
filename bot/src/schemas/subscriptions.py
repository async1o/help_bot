"""Pydantic схема для подписок."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SubscriptionSchema(BaseModel):
    user_id: str
    is_subscribed: bool = False
    subscribed_at: Optional[datetime] = None
    unsubscribed_at: Optional[datetime] = None
    last_checked_at: Optional[datetime] = None
