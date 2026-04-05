from aiogram.filters import BaseFilter
from aiogram.types import Message

from src.db.repositories import UserRepository

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if not message.from_user:
            return False

        user = await UserRepository().get_user_by_id(user_id=str(message.from_user.id))
        if user is None:
            return False
        return user.is_admin
    