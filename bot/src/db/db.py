import logging

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from src.utils.config import settings

logger = logging.getLogger('Database')

engine = create_async_engine(
    url = settings.get_url_db,
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass


# Импортируем все модели, чтобы они были зарегистрированы в Base.metadata
# ДО вызова create_all
def _import_all_models():
    from src.models.users import UserModel  # noqa: F401
    from src.models.messages import MsgModel  # noqa: F401
    from src.models.dialogs import DialogModel  # noqa: F401
    from src.models.payments import PaymentModel  # noqa: F401
    from src.models.subscriptions import SubscriptionModel  # noqa: F401


async def _table_exists(table_name: str) -> bool:
    """Проверить, существует ли конкретная таблица в БД."""
    async with engine.connect() as conn:
        def _check(sync_conn):
            insp = inspect(sync_conn)
            return table_name in insp.get_table_names()
        return await conn.run_sync(_check)


async def _column_exists(table_name: str, column_name: str) -> bool:
    """Проверить, существует ли колонка в таблице."""
    async with engine.connect() as conn:
        def _check(sync_conn):
            insp = inspect(sync_conn)
            columns = [col['name'] for col in insp.get_columns(table_name)]
            return column_name in columns
        return await conn.run_sync(_check)


async def _apply_migrations():
    """Применить миграции для существующих таблиц."""
    # Добавляем is_paid, если нет
    if await _table_exists('users') and not await _column_exists('users', 'is_paid'):
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE users ADD COLUMN is_paid BOOLEAN DEFAULT FALSE"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN paid_at TIMESTAMP DEFAULT NULL"))
            logger.info('Migration applied: added is_paid and paid_at to users')

    # Добавляем paid_at, если нет (на случай если is_paid уже был)
    if await _table_exists('users') and not await _column_exists('users', 'paid_at'):
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE users ADD COLUMN paid_at TIMESTAMP DEFAULT NULL"))
            logger.info('Migration applied: added paid_at to users')

    # Добавляем has_paid_ever — навсегда запоминаем факт оплаты
    if await _table_exists('users') and not await _column_exists('users', 'has_paid_ever'):
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE users ADD COLUMN has_paid_ever BOOLEAN DEFAULT FALSE"))
            # Для тех, кто уже оплатил (is_paid=True), ставим has_paid_ever=True
            await conn.execute(text("UPDATE users SET has_paid_ever = TRUE WHERE is_paid = TRUE"))
            logger.info('Migration applied: added has_paid_ever to users')

    # Создаём таблицу subscriptions, если нет
    if not await _table_exists('subscriptions'):
        logger.info('Table subscriptions does not exist, will be created by create_all')


async def create_tables_if_not_exists():
    """Создать таблицы, если они ещё не существуют."""
    _import_all_models()

    # Применяем миграции для существующих таблиц
    await _apply_migrations()

    # Проверяем наличие ключевой таблицы (например, dialogs — самой новой)
    if not await _table_exists('dialogs'):
        await create_tables()
        logger.info('Tables created on startup (auto)')
    else:
        logger.info('Tables already exist, skipping creation')


async def create_tables():
    _import_all_models()
    from src.db.repositories import AdminRepository

    async with engine.begin() as eng:
        await eng.run_sync(Base.metadata.create_all)
    await AdminRepository().add_start_admins()
    logger.info('Tables created')

async def reset_tables():
    _import_all_models()
    async with engine.begin() as eng:
        await eng.run_sync(Base.metadata.drop_all)
    await create_tables()
    logger.info('Tables reset')
    