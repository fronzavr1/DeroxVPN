print("=== db/models.py: начало загрузки ===", flush=True)

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import Base, async_session, engine

print("=== db/models.py: импорты из database выполнены ===", flush=True)


class DatabaseMiddleware(BaseMiddleware):
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
    tariff = Column(String)
    time_sub = Column(DateTime(timezone=True))
    link = Column(String)


class PriceData(Base):
    __tablename__ = "price_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(Integer, default=100)
    sixmonth = Column(Integer, default=500)
    year = Column(Integer, default=1000)


class Stats(Base):
    __tablename__ = "stats"
    id = Column(Integer, primary_key=True)
    total_money = Column(BigInteger, default=0)
    monthly_subs = Column(BigInteger, default=0)
    sixmonthly_subs = Column(BigInteger, default=0)
    yearly_subs = Column(BigInteger, default=0)


async def create_tables():
    print("=== create_tables(): создание таблиц ===", flush=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("=== create_tables(): таблицы созданы ===", flush=True)
