print("=== database.py: начало загрузки ===", flush=True)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import DATABASE_URL

print(f"=== database.py: DATABASE_URL = {DATABASE_URL[:30]}... ===", flush=True)

# Преобразуем синхронный URL в асинхронный
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
print("=== database.py: URL преобразован ===", flush=True)

# Создаём асинхронный движок
engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
print("=== database.py: engine создан ===", flush=True)

# Создаём фабрику сессий
async_session = async_sessionmaker(engine, expire_on_commit=False)
print("=== database.py: async_session создан ===", flush=True)

# Базовый класс для моделей
Base = declarative_base()
print("=== database.py: Base создан, загрузка завершена ===", flush=True)
