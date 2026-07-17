print("=== db/models.py: начало загрузки ===", flush=True)

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from config import DATABASE_URL

print(f"=== db/models.py: DATABASE_URL = {DATABASE_URL[:30]}... ===", flush=True)

# Преобразуем синхронный URL в асинхронный
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
print("=== db/models.py: URL преобразован ===", flush=True)

# Создаём асинхронный движок
engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
print("=== db/models.py: engine создан ===", flush=True)

Base = declarative_base()
print("=== db/models.py: Base создан ===", flush=True)

# Создаём фабрику сессий
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
print("=== db/models.py: async_session создан ===", flush=True)


class DatabaseMiddleware(BaseMiddleware):  # Мидлварь для внедрения сессии базы данных в обработчики
    async def __call__(self, handler, event: TelegramObject, data: dict):
        print("=== DatabaseMiddleware: вызов ===", flush=True)
        async with async_session() as session:
            data["session"] = session
            return await handler(event, data)


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    fullname = Column(String, nullable=False)
    tariff = Column(String)  # Купленный тариф
    time_sub = Column(DateTime(timezone=True))  # Время до окончания подписки
    link = Column(String)  # Выданная пользователю ссылка


class PriceData(Base):
    __tablename__ = "price_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(Integer, default=100)
    sixmonth = Column(Integer, default=500)
    year = Column(Integer, default=1000)


class Stats(Base):
    __tablename__ = "stats"
    id = Column(Integer, primary_key=True)
    total_money = Column(BigInteger, default=0)  # Общая сумма полученных денег
    monthly_subs = Column(BigInteger, default=0)  # Кол-во купивших за месяц
    sixmonthly_subs = Column(BigInteger, default=0)
    yearly_subs = Column(BigInteger, default=0)


async def create_tables():
    print("=== create_tables(): создание таблиц ===", flush=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("=== create_tables(): таблицы созданы ===", flush=True)
