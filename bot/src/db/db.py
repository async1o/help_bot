import logging

from sqlalchemy import inspect
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


async def _table_exists(table_name: str) -> bool:
    """Проверить, существует ли конкретная таблица в БД."""
    async with engine.connect() as conn:
        def _check(sync_conn):
            insp = inspect(sync_conn)
            return table_name in insp.get_table_names()
        return await conn.run_sync(_check)


async def create_tables_if_not_exists():
    """Создать таблицы, если они ещё не существуют."""
    _import_all_models()

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
    