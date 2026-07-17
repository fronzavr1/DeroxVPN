print("=== config.py: загрузка начата ===", flush=True)

import pytz
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from environs import Env

print("=== config.py: импорты выполнены ===", flush=True)

env = Env()
env.read_env('.env')
print("=== config.py: .env загружен ===", flush=True)

TOKEN = env.str('TOKEN')
OWNER_ID = env.int('ADMIN')
CHANNEL_ID = env.int('PRIVATE_CHANNEL_ID')
CHAT_ID = env.int('PRIVATE_CHAT_ID')

MSK = pytz.timezone('Europe/Moscow')
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

print("=== config.py: bot и dp созданы ===", flush=True)
print("=== config.py: загрузка завершена ===", flush=True)
