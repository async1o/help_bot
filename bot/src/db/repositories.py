import logging
import time
from datetime import datetime

from sqlalchemy import insert, select, update, delete
from sqlalchemy.exc import IntegrityError

from src.db.db import async_session_maker
from src.models.users import UserModel
from src.models.messages import MsgModel
from src.models.dialogs import DialogModel
from src.models.payments import PaymentModel
from src.models.subscriptions import SubscriptionModel
from src.schemas.users import UserSchema
from src.schemas.messages import MsgSchema
from src.schemas.dialogs import DialogSchema
from src.schemas.payments import PaymentSchema
from src.schemas.subscriptions import SubscriptionSchema
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
            except IntegrityError as e:
                logger.warning('User %s already exists (IntegrityError): %s', user.user_id, e)
            except Exception as e:
                logger.error('Unexpected error adding user %s: %s', user.user_id, e)
    
class AdminRepository:
    _operators_cache: list | None = None
    _operators_cache_ts: float = 0
    _OPERATORS_CACHE_TTL = 30.0  # секунд

    @classmethod
    def invalidate_operators_cache(cls) -> None:
        """Принудительно сбросить кэш операторов."""
        cls._operators_cache = None
        cls._operators_cache_ts = 0

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
            AdminRepository.invalidate_operators_cache()

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


class DialogRepository:
    """Репозиторий для управления активными диалогами (персистентное хранение в БД)."""

    async def add_dialog(self, dialog: DialogSchema) -> None:
        """Начать диалог. Если у оператора или sender уже есть диалог — он заменяется."""
        async with async_session_maker() as session:
            # Удаляем существующий диалог для этого оператора
            await session.execute(
                delete(DialogModel).where(DialogModel.operator_id == dialog.operator_id)
            )
            # Удаляем существующий диалог для этого sender (если он в другом диалоге)
            await session.execute(
                delete(DialogModel).where(DialogModel.sender_id == dialog.sender_id)
            )
            stmt = insert(DialogModel).values(dialog.model_dump())
            await session.execute(stmt)
            await session.commit()
            logger.info('Dialog added: operator=%s, sender=%s', dialog.operator_id, dialog.sender_id)

    async def remove_by_operator(self, operator_id: str) -> str | None:
        """Удалить диалог по оператору. Возвращает sender_id или None."""
        async with async_session_maker() as session:
            stmt = select(DialogModel.sender_id).where(DialogModel.operator_id == operator_id)
            result = await session.execute(stmt)
            sender_id = result.scalar_one_or_none()
            if sender_id:
                await session.execute(
                    delete(DialogModel).where(DialogModel.operator_id == operator_id)
                )
                await session.commit()
                return sender_id
            return None

    async def remove_by_user(self, sender_id: str) -> str | None:
        """Удалить диалог по пользователю. Возвращает operator_id или None."""
        async with async_session_maker() as session:
            stmt = select(DialogModel.operator_id).where(DialogModel.sender_id == sender_id)
            result = await session.execute(stmt)
            operator_id = result.scalar_one_or_none()
            if operator_id:
                await session.execute(
                    delete(DialogModel).where(DialogModel.sender_id == sender_id)
                )
                await session.commit()
                return operator_id
            return None

    async def get_user_by_operator(self, operator_id: str) -> str | None:
        async with async_session_maker() as session:
            stmt = select(DialogModel.sender_id).where(DialogModel.operator_id == operator_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_operator_by_user(self, sender_id: str) -> str | None:
        async with async_session_maker() as session:
            stmt = select(DialogModel.operator_id).where(DialogModel.sender_id == sender_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def is_operator_in_dialog(self, operator_id: str) -> bool:
        async with async_session_maker() as session:
            stmt = select(DialogModel.id).where(DialogModel.operator_id == operator_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def is_user_in_dialog(self, sender_id: str) -> bool:
        async with async_session_maker() as session:
            stmt = select(DialogModel.id).where(DialogModel.sender_id == sender_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None


class PaymentRepository:
    """Репозиторий для управления платежами."""

    async def add_payment(self, payment: PaymentSchema) -> None:
        async with async_session_maker() as session:
            stmt = insert(PaymentModel).values(payment.model_dump())
            try:
                await session.execute(stmt)
                await session.commit()
                logger.info('Payment recorded: user=%s, charge=%s', payment.user_id, payment.telegram_payment_charge_id)
            except IntegrityError:
                await session.rollback()
                logger.warning('Payment %s already exists (IntegrityError), skipping', payment.telegram_payment_charge_id)

    async def activate_user_subscription(self, user_id: str) -> None:
        """Активировать подписку и отметить что пользователь когда-либо оплачивал."""
        async with async_session_maker() as session:
            stmt = update(UserModel).where(UserModel.user_id == user_id).values(
                is_paid=True,
                has_paid_ever=True,
                paid_at=datetime.utcnow()
            )
            await session.execute(stmt)
            await session.commit()
            logger.info('Subscription activated for user=%s (has_paid_ever=True)', user_id)


class SubscriptionRepository:
    """Репозиторий для управления подписками пользователей на канал."""

    async def get_subscription(self, user_id: str) -> SubscriptionModel | None:
        """Получить подписку пользователя."""
        async with async_session_maker() as session:
            stmt = select(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create_or_update_subscription(self, user_id: str, is_subscribed: bool) -> SubscriptionModel:
        """Создать или обновить подписку. Возвращает объект подписки."""
        async with async_session_maker() as session:
            existing = await self.get_subscription(user_id)
            if existing:
                # Обновляем существующую запись
                updates = {
                    'is_subscribed': is_subscribed,
                    'last_checked_at': datetime.utcnow(),
                }
                if is_subscribed:
                    updates['subscribed_at'] = datetime.utcnow()
                    updates['unsubscribed_at'] = None
                else:
                    updates['unsubscribed_at'] = datetime.utcnow()

                stmt = update(SubscriptionModel).where(SubscriptionModel.user_id == user_id).values(**updates)
                await session.execute(stmt)
                await session.commit()

                # Возвращаем обновлённый объект
                stmt = select(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
                result = await session.execute(stmt)
                return result.scalar_one()
            else:
                # Создаём новую запись
                now = datetime.utcnow()
                sub = SubscriptionSchema(
                    user_id=user_id,
                    is_subscribed=is_subscribed,
                    subscribed_at=now if is_subscribed else None,
                    unsubscribed_at=None if is_subscribed else now,
                    last_checked_at=now,
                )
                stmt = insert(SubscriptionModel).values(sub.model_dump())
                await session.execute(stmt)
                await session.commit()

                stmt = select(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
                result = await session.execute(stmt)
                return result.scalar_one()

    async def mark_subscribed(self, user_id: str) -> SubscriptionModel:
        """Отметить пользователя как подписанного."""
        return await self.create_or_update_subscription(user_id, is_subscribed=True)

    async def mark_unsubscribed(self, user_id: str) -> SubscriptionModel:
        """Отметить пользователя как отписавшегося."""
        return await self.create_or_update_subscription(user_id, is_subscribed=False)

    async def is_user_subscribed(self, user_id: str) -> bool:
        """Проверить, подписан ли пользователь на канал."""
        sub = await self.get_subscription(user_id)
        if sub is None:
            return False
        return sub.is_subscribed

