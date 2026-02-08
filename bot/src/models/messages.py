from sqlalchemy.orm import Mapped, mapped_column

from src.db.db import Base


class MsgModel(Base):
    """Сообщение «новый запрос», отправленное оператору (для удаления при принятии)."""
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(index=True)  # Уникальный ID обращения (UUID)
    message_id: Mapped[int] = mapped_column()
    operator_id: Mapped[str] = mapped_column()
    sender_id: Mapped[str] = mapped_column()