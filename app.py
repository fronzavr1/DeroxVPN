import sys
print("=== ШАГ 1: Python запущен ===", flush=True)
print(f"Python version: {sys.version}", flush=True)

print("=== ШАГ 2: Начинаем импорт config ===", flush=True)
from config import bot, dp
print("=== ШАГ 3: config загружен ===", flush=True)

print("=== ШАГ 4: Начинаем импорт database ===", flush=True)
from db.database import async_session  # <-- ИМПОРТИРУЕМ ОТСЮДА
print("=== ШАГ 5: database загружен ===", flush=True)

print("=== ШАГ 6: Начинаем импорт db.models ===", flush=True)
from db.models import create_tables, DatabaseMiddleware
print("=== ШАГ 7: db.models загружен ===", flush=True)

# ... остальной код без изменений
