"""SQLAlchemy-модель для активных диалогов (один оператор — один пользователь)."""

from sqlalchemy.orm import Mapped, mapped_column

from src.db.db import Base


class DialogModel(Base):
    __tablename__ = "dialogs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operator_id: Mapped[str] = mapped_column(unique=True, index=True)
    sender_id: Mapped[str] = mapped_column(index=True)
