"""SQLAlchemy-модель для записей о платежах."""

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from src.db.db import Base


class PaymentModel(Base):
    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(index=True)
    telegram_payment_charge_id: Mapped[str] = mapped_column(unique=True)
    amount: Mapped[int]  # в минорных единицах (копейки)
    currency: Mapped[str] = mapped_column(default='RUB')
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
