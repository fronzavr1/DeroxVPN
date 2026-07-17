print("=== database.py: начало загрузки ===", flush=True)

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Берём DATABASE_URL напрямую из переменных окружения, без импорта config
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL не установлен!")

print(f"=== database.py: DATABASE_URL = {DATABASE_URL[:30]}... ===", flush=True)

# Преобразуем в асинхронный URL
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
print("=== database.py: URL преобразован ===", flush=True)

engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
print("=== database.py: engine создан ===", flush=True)

Base = declarative_base()
print("=== database.py: Base создан ===", flush=True)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
print("=== database.py: async_session создан ===", flush=True)

print("=== database.py: загрузка завершена ===", flush=True)
