from datetime import datetime
from pydantic import BaseModel


class PaymentSchema(BaseModel):
    user_id: str
    telegram_payment_charge_id: str
    amount: int
    currency: str = 'RUB'
    created_at: datetime = datetime.utcnow()
