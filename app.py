import sys
print("=== ШАГ 1: Python запущен ===", flush=True)
print(f"Python version: {sys.version}", flush=True)

print("=== ШАГ 2: Начинаем импорт config ===", flush=True)
from config import DATABASE_URL
print(f"=== ШАГ 3: DATABASE_URL загружен ===", flush=True)

print("=== ШАГ 4: Начинаем импорт database ===", flush=True)
from db.models import create_tables, DatabaseMiddleware, async_session
print("=== ШАГ 5: database импортирован ===", flush=True)

print("=== ШАГ 6: Начинаем импорт остальных модулей ===", flush=True)
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import bot, dp
from handlers.admin import without_adding, stats, setprice
from handlers.user import start, tariff, sub_info, expiration_check, stars_payment
from handlers.user.expiration_check import check_subscriptions, check_expired_subscriptions
print("=== ШАГ 7: Все импорты выполнены ===", flush=True)

logging.getLogger('aiogram').setLevel(logging.INFO)

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')  # Часовой пояс - МСК


async def main():
    print("=== ШАГ 8: Запуск main() ===", flush=True)
    print("=== ШАГ 9: Создание таблиц ===", flush=True)
    await create_tables()
    print("=== ШАГ 10: Таблицы созданы ===", flush=True)
    
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.include_routers(start.router, without_adding.router, tariff.router, stats.router, stars_payment.router,
                       sub_info.router, expiration_check.router, setprice.router)

    print("=== ШАГ 11: Инициализация тарифов ===", flush=True)
    async with async_session() as session:
        await tariff.init_tariffs(session)
    print("=== ШАГ 12: Тарифы инициализированы ===", flush=True)

    try:
        print("=== ШАГ 13: Настройка scheduler ===", flush=True)
        scheduler.add_job(check_subscriptions, 'cron', hour=10, minute=00)  # Проверка на то, остался ли день до окончания подписки. Ежедневно в 10:00
        scheduler.add_job(check_expired_subscriptions, 'interval', minutes=15)  # Проверка на уже истёчную подписку каждые 15 минут
        scheduler.start()
        print("=== ШАГ 14: Scheduler запущен ===", flush=True)

        print("=== ШАГ 15: Удаление webhook ===", flush=True)
        await bot.delete_webhook(drop_pending_updates=True)
        print(f'=== ШАГ 16: Бот запущен. ===')
        await dp.start_polling(bot)
    except Exception as e:
        logging.exception(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    print("=== ШАГ 0: Запуск скрипта ===", flush=True)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, RuntimeError) as main_error:
        print('Бот выключен.')
