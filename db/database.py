print("=== db/models.py: начало загрузки ===", flush=True)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import DATABASE_URL

print(f"=== db/models.py: DATABASE_URL = {DATABASE_URL[:30]}... ===", flush=True)

# Преобразуем синхронный URL в асинхронный
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
print("=== db/models.py: URL преобразован ===", flush=True)

# Создаём асинхронный движок
engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
print("=== db/models.py: engine создан ===", flush=True)

# Создаём фабрику сессий
async_session = async_sessionmaker(engine, expire_on_commit=False)
print("=== db/models.py: async_session создан ===", flush=True)

# Базовый класс для моделей
Base = declarative_base()
print("=== db/models.py: Base создан, загрузка завершена ===", flush=True)

async def create_tables():
    print("=== create_tables(): создание таблиц ===", flush=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("=== create_tables(): таблицы созданы ===", flush=True)

class DatabaseMiddleware:
    async def __call__(self, handler, event, data):
        print("=== DatabaseMiddleware: вызов ===", flush=True)
        async with async_session() as session:
            data['session'] = session
            return await handler(event, data)
