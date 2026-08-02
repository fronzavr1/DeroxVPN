from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice, FSInputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import pytz

from db.models import Users

router = Router()
MSK = pytz.timezone('Europe/Moscow')

# 👇 ТВОЙ ЮЗЕРНЕЙМ (без @)
ADMIN_USERNAME = "DeroXHelper"


def now_moscow():
    return datetime.now(MSK)


# ============================================
# ПРОБНЫЙ ПЕРИОД
# ============================================
@router.callback_query(lambda c: c.data == "free_trial")
async def free_trial_handler(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    username = callback.from_user.username
    now = now_moscow()

    print(f"🔥 free_trial_handler ВЫЗВАН! user_id={user_id}, username={username}")

    # ⭐ ЕСЛИ ЭТО АДМИН
    if username and username.lower() == ADMIN_USERNAME.lower():
        print(f"✅ АДМИН ОПОЗНАН! {username}")
        try:
            user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
            if not user:
                user = Users(user_id=user_id, fullname=callback.from_user.full_name)
                session.add(user)

            user.time_sub = now + timedelta(days=3)
            user.tariff = "👑 Админ (пробный 3 дня)"
            user.trial_used = False
            await session.commit()
            print(f"✅ Админу {username} выдан пробный период до {user.time_sub}")

            try:
                config_file = FSInputFile("configs/trial.json", filename="derox_vpn_trial.json")
                await callback.message.answer_document(
                    document=config_file,
                    caption=f"👑 <b>Админский пробный период активирован!</b>\n\n"
                            f"✅ Доступ на <b>3 дня</b>\n"
                            f"📅 Активен до: <b>{(now + timedelta(days=3)).strftime('%d.%m.%Y %H:%M')}</b>\n\n"
                            f"📥 Скачайте файл и импортируйте в VPN.\n"
                            f"🔄 Можно активировать снова в любой момент.",
                    parse_mode=ParseMode.HTML
                )
                print("✅ Конфиг отправлен админу")
            except FileNotFoundError:
                await callback.message.answer("❌ Ошибка: файл конфига не найден.")
                print("❌ Файл configs/trial.json не найден!")

            await callback.answer()
            return

        except Exception as e:
            print(f"❌ ОШИБКА В БЛОКЕ АДМИНА: {e}")
            await callback.message.answer(f"❌ Ошибка: {e}")
            await callback.answer()
            return

    # ⬇️ ОБЫЧНАЯ ЛОГИКА ДЛЯ ВСЕХ ОСТАЛЬНЫХ
    print(f"Обычный пользователь {user_id}")
    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()

    if user and user.time_sub and user.time_sub > now:
        await callback.message.answer("❌ У вас уже есть активная подписка!")
        await callback.answer()
        return

    if user and user.trial_used:
        await callback.message.answer("❌ Вы уже использовали пробный период!")
        await callback.answer()
        return

    if not user:
        user = Users(user_id=user_id, fullname=callback.from_user.full_name)
        session.add(user)

    user.time_sub = now + timedelta(days=3)
    user.tariff = "Пробный (3 дня)"
    user.trial_used = True
    await session.commit()

    try:
        config_file = FSInputFile("configs/trial.json", filename="derox_vpn_trial.json")
        await callback.message.answer_document(
            document=config_file,
            caption=f"🎉 <b>Пробный период активирован!</b>\n\n"
                    f"✅ Доступ на <b>3 дня</b>\n"
                    f"📅 Активен до: <b>{(now + timedelta(days=3)).strftime('%d.%m.%Y %H:%M')}</b>\n\n"
                    f"📥 Скачайте файл и импортируйте в ваше VPN-приложение.",
            parse_mode=ParseMode.HTML
        )
    except FileNotFoundError:
        await callback.message.answer("❌ Ошибка: файл конфига не найден.")

    await callback.answer()


# ============================================
# ОПЛАТА STARS
# ============================================
@router.callback_query(lambda c: c.data.startswith("tariff_"))
async def tariff_callback(callback: CallbackQuery):
    tariff_key = callback.data.replace("tariff_", "")

    tariff_map = {
        "month":    {"days": 31,  "price": 100, "name": "🌙 1 месяц"},
        "sixmonth": {"days": 186, "price": 500, "name": "🌕 6 месяцев"},
        "year":     {"days": 365, "price": 1000, "name": "🌚 1 год"}
    }

    tariff = tariff_map.get(tariff_key)
    if not tariff:
        await callback.answer("❌ Неверный тариф")
        return

    await callback.message.answer_invoice(
        title=f"DeroX VPN — {tariff['name']}",
        description=f"Доступ к VPN на {tariff['days']} дней",
        payload=tariff_key,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=tariff['name'], amount=tariff['price'])],
        start_parameter="derox_vpn_subscription"
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout: PreCheckoutQuery):
    await pre_checkout.answer(ok=True)


@router.message(lambda message: message.successful_payment)
async def successful_payment_handler(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    payment_info = message.successful_payment
    now = now_moscow()

    tariff_key = payment_info.invoice_payload

    tariff_map = {
        "month":    {"days": 31,  "file": "configs/month.json",   "name": "🌙 1 месяц"},
        "sixmonth": {"days": 186, "file": "configs/sixmonth.json", "name": "🌕 6 месяцев"},
        "year":     {"days": 365, "file": "configs/year.json",    "name": "🌚 1 год"}
    }

    tariff = tariff_map.get(tariff_key)
    if not tariff:
        await message.answer("❌ Ошибка: тариф не найден")
        return

    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    if not user:
        user = Users(user_id=user_id, fullname=message.from_user.full_name)
        session.add(user)

    if user.time_sub and user.time_sub > now:
        user.time_sub = user.time_sub + timedelta(days=tariff["days"])
    else:
        user.time_sub = now + timedelta(days=tariff["days"])

    user.tariff = tariff["name"]
    await session.commit()

    try:
        config_file = FSInputFile(tariff["file"], filename=f"derox_vpn_{tariff_key}.json")
        await message.answer_document(
            document=config_file,
            caption=f"✅ <b>Оплата прошла успешно!</b>\n\n"
                    f"📦 Тариф: {tariff['name']}\n"
                    f"📅 Подписка активна до: <b>{user.time_sub.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
                    f"📥 Скачайте файл и импортируйте в ваше VPN-приложение.",
            parse_mode=ParseMode.HTML
        )
    except FileNotFoundError:
        await message.answer("❌ Ошибка: файл конфига не найден.")


# ============================================
# ПОЛУЧИТЬ КОНФИГ
# ============================================
@router.callback_query(lambda c: c.data == "get_config")
async def get_config_handler(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    username = callback.from_user.username
    now = now_moscow()

    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()

    # Если админ — даём конфиг всегда
    if username and username.lower() == ADMIN_USERNAME.lower():
        if not user:
            user = Users(user_id=user_id, fullname=callback.from_user.full_name)
            session.add(user)
            user.time_sub = now + timedelta(days=3)
            user.tariff = "👑 Админ (пробный)"
            user.trial_used = False
            await session.commit()

        if not user.time_sub or user.time_sub <= now:
            user.time_sub = now + timedelta(days=3)
            user.tariff = "👑 Админ (продлен)"
            await session.commit()

        try:
            config_file = FSInputFile("configs/trial.json", filename=f"derox_vpn_admin.json")
            await callback.message.answer_document(
                document=config_file,
                caption=f"👑 <b>Админский конфиг</b>\n\n"
                        f"📦 Тариф: {user.tariff}\n"
                        f"📅 Активен до: <b>{user.time_sub.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
                        f"🔄 Можно обновить в любой момент.",
                parse_mode=ParseMode.HTML
            )
        except FileNotFoundError:
            await callback.message.answer("❌ Ошибка: файл конфига не найден.")

        await callback.answer()
        return

    # ⬇️ ОБЫЧНАЯ ЛОГИКА
    if not user or not user.time_sub or user.time_sub <= now:
        await callback.message.answer(
            "❌ У вас нет активной подписки.\n\nОформите подписку в меню «Подписка».",
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        return

    tariff_map = {
        "🌙 1 месяц": "month.json",
        "🌕 6 месяцев": "sixmonth.json",
        "🌚 1 год": "year.json",
        "Пробный (3 дня)": "trial.json"
    }

    filename = tariff_map.get(user.tariff, "trial.json")

    try:
        config_file = FSInputFile(f"configs/{filename}", filename=f"derox_vpn_{user.user_id}.json")
        await callback.message.answer_document(
            document=config_file,
            caption=f"🔑 <b>Ваш конфиг</b>\n\n"
                    f"📦 Тариф: {user.tariff}\n"
                    f"📅 Активен до: <b>{user.time_sub.strftime('%d.%m.%Y %H:%M') if user.time_sub else 'Не указано'}</b>",
            parse_mode=ParseMode.HTML
        )
    except FileNotFoundError:
        await callback.message.answer("❌ Ошибка: файл конфига не найден.")

    await callback.answer()
