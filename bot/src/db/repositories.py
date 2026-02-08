import logging
import time

from sqlalchemy import insert, select, update, delete

from src.db.db import async_session_maker
from src.models.users import UserModel
from src.models.messages import MsgModel
from src.schemas.users import UserSchema
from src.schemas.messages import MsgSchema
from src.utils.config import settings

logger = logging.getLogger('Repositories')

class UserRepository:
    async def get_user_by_id(self, user_id: str):
        async with async_session_maker() as session:

            stmt = select(UserModel).where(UserModel.user_id == user_id)
            res = (await session.execute(stmt)).scalar()
            logger.info(msg='User handled from DB')


            return res

    async def add_user(self, user: UserSchema):
        async with async_session_maker() as session:
            
            stmt = insert(UserModel).values(user.model_dump())
            
            
            try:
                await session.execute(stmt)
                await session.commit()
                logger.info(msg='User added to DB')
            except:
                pass
    
class AdminRepository:
    _operators_cache: list | None = None
    _operators_cache_ts: float = 0
    _OPERATORS_CACHE_TTL = 30.0  # секунд

    async def add_start_admins(self):
        for admin_id in settings.ADMINS.split(','):
            await UserRepository().add_user(
                UserSchema(
                    user_id=admin_id,
                    is_admin=True,
                    is_operator=False
                )
            )
        logger.info(msg='Admins added to DB')

    async def get_admins(self):
        async with async_session_maker() as session:
            stmt = select(UserModel.user_id).where(UserModel.is_admin == True)
            res = await session.execute(stmt)
            return res.all()

    async def update_roles(self, user_id: str, add: bool, operator: bool):
        if not await UserRepository().get_user_by_id(user_id):
            raise NotImplementedError
        async with async_session_maker() as session:
            role = 'is_operator' if operator else 'is_admin'
            stmt = update(UserModel).where(UserModel.user_id == user_id).values({role: add})
            await session.execute(stmt)
            await session.commit()
        if operator:
            AdminRepository._operators_cache = None

    async def get_all_operators(self) -> list:
        now = time.monotonic()
        if (
            AdminRepository._operators_cache is not None
            and (now - AdminRepository._operators_cache_ts) < self._OPERATORS_CACHE_TTL
        ):
            return AdminRepository._operators_cache
        async with async_session_maker() as session:
            stmt = select(UserModel.user_id).where(UserModel.is_operator == True)
            res = (await session.execute(stmt)).all()
            AdminRepository._operators_cache = res
            AdminRepository._operators_cache_ts = now
            return res

class MsgRepository:
    async def add_message(self, message: MsgSchema) -> None:
        async with async_session_maker() as session:
            stmt = insert(MsgModel).values(message.model_dump())
            await session.execute(stmt)
            await session.commit()

    async def get_by_request_id(self, request_id: str) -> list[MsgModel]:
        """Все записи сообщений по одному обращению (по одному оператору — одна запись)."""
        async with async_session_maker() as session:
            stmt = select(MsgModel).where(MsgModel.request_id == request_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def delete_by_request_id(self, request_id: str) -> None:
        async with async_session_maker() as session:
            stmt = delete(MsgModel).where(MsgModel.request_id == request_id)
            await session.execute(stmt)
            await session.commit()

