import sys
print("=== TEST: Python запущен ===", flush=True)
sys.stdout.flush()

print("=== TEST: Импортируем config ===", flush=True)
from config import bot, dp
print("=== TEST: config импортирован ===", flush=True)

print("=== TEST: Импортируем db.database ===", flush=True)
from db.database import async_session
print("=== TEST: db.database импортирован ===", flush=True)

print("=== TEST: Импортируем db.models ===", flush=True)
from db.models import create_tables, DatabaseMiddleware
print("=== TEST: db.models импортирован ===", flush=True)

print("=== TEST: Импортируем handlers ===", flush=True)
from handlers.admin import without_adding, stats, setprice
print("=== TEST: handlers.admin импортирован ===", flush=True)

from handlers.user import start, tariff, sub_info, expiration_check, stars_payment
print("=== TEST: handlers.user импортирован ===", flush=True)

from handlers.user.expiration_check import check_subscriptions, check_expired_subscriptions
print("=== TEST: handlers.user.expiration_check импортирован ===", flush=True)

print("=== TEST: ВСЕ ИМПОРТЫ УСПЕШНЫ! ===", flush=True)