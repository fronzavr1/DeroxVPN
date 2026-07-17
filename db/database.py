from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import DATABASE_URL

# Преобразуем синхронный URL в асинхронный
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Создаём асинхронный движок
engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)

# Создаём фабрику сессий
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Базовый класс для моделей
Base = declarative_base()
