import sys
print("=== ШАГ 1: Python запущен ===", flush=True)

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import bot, dp
from db.database import async_session
from db.models import create_tables, DatabaseMiddleware
from handlers.admin import without_adding_router, stats_router, setprice_router
from handlers.user import start_router, tariff_router, sub_info_router, expiration_check_router, stars_payment_router
from handlers.user.tariff import init_tariffs  # <-- ЭТОТ ИМПОРТ НУЖЕН!
from handlers.user.expiration_check import check_subscriptions, check_expired_subscriptions

print("=== ШАГ 2: Все импорты выполнены ===", flush=True)

logging.getLogger('aiogram').setLevel(logging.INFO)

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')


async def main():
    print("=== ШАГ 3: Запуск main() ===", flush=True)
    await create_tables()
    print("=== ШАГ 4: Таблицы созданы ===", flush=True)
    
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.include_routers(
        start_router,
        without_adding_router,
        tariff_router,
        stats_router,
        stars_payment_router,
        sub_info_router,
        expiration_check_router,
        setprice_router
    )

    print("=== ШАГ 5: Инициализация тарифов ===", flush=True)
    async with async_session() as session:
        await init_tariffs(session)  # <-- ЗДЕСЬ ТОЖЕ ИСПРАВЛЕНО!
    print("=== ШАГ 6: Тарифы инициализированы ===", flush=True)

    try:
        print("=== ШАГ 7: Настройка scheduler ===", flush=True)
        scheduler.add_job(check_subscriptions, 'cron', hour=10, minute=00)
        scheduler.add_job(check_expired_subscriptions, 'interval', minutes=15)
        scheduler.start()
        print("=== ШАГ 8: Scheduler запущен ===", flush=True)

        await bot.delete_webhook(drop_pending_updates=True)
        print('✅ БОТ УСПЕШНО ЗАПУЩЕН!')
        await dp.start_polling(bot)
    except Exception as e:
        logging.exception(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    print("=== ШАГ 0: Запуск скрипта ===", flush=True)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, RuntimeError):
        print('Бот выключен.')
