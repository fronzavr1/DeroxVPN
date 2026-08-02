from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice, FSInputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import pytz
import secrets
import string

from db.models import Users

router = Router()
MSK = pytz.timezone('Europe/Moscow')


def now_moscow():
    return datetime.now(MSK)


# ============================================
# ПРОБНЫЙ ПЕРИОД
# ============================================
@router.callback_query(lambda c: c.data == "free_trial")
async def free_trial_handler(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    now = now_moscow()
    
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
