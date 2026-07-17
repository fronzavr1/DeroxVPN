from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice, FSInputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import pytz

from db.models import Users
from handlers.user.tariff import tariff_manager

router = Router()
MSK = pytz.timezone('Europe/Moscow')


def now_moscow():
    return datetime.now(MSK)


# ============================================
# ПРОБНЫЙ ПЕРИОД (3 дня)
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
    
    config_file = FSInputFile("configs/trial.json", filename="derox_vpn_trial.json")
    
    await callback.message.answer_document(
        document=config_file,
        caption=f"🎉 <b>Пробный период активирован!</b>\n\n"
                f"✅ Доступ на <b>3 дня</b>\n"
                f"📅 Активен до: <b>{(now + timedelta(days=3)).strftime('%d.%m.%Y %H:%M')}</b>\n\n"
                f"📥 Скачайте файл и импортируйте его в ваше VPN-приложение (Xray/V2Ray).\n\n"
                f"⚠️ После окончания срока файл перестанет работать.",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


# ============================================
# ОПЛАТА STARS
# ============================================
@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout: PreCheckoutQuery):
    await pre_checkout.answer(ok=True)


@router.message(lambda message: message.successful_payment)
async def successful_payment_handler(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    payment_info = message.successful_payment
    now = now_moscow()
    
    payload = payment_info.invoice_payload
    parts = payload.split('_')
    tariff_key = parts[2] if len(parts) >= 3 else "month"
    
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
    
    config_file = FSInputFile(tariff["file"], filename=f"derox_vpn_{tariff_key}.json")
    
    await message.answer_document(
        document=config_file,
        caption=f"✅ <b>Оплата прошла успешно!</b>\n\n"
                f"📦 Тариф: {tariff['name']}\n"
                f"📅 Подписка активна до: <b>{user.time_sub.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
                f"📥 Скачайте файл и импортируйте его в ваше VPN-приложение (Xray/V2Ray).\n\n"
                f"⚠️ После окончания срока файл перестанет работать.",
        parse_mode=ParseMode.HTML
    )


# ============================================
# ПОЛУЧИТЬ МОЙ КОНФИГ
# ============================================
@router.callback_query(lambda c: c.data == "get_config")
async def get_config_handler(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    now = now_moscow()
    
    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    
    if not user or not user.time_sub or user.time_sub <= now:
        await callback.message.answer(
            "❌ У вас нет активной подписки.\n\n"
            "Оформите подписку в меню «Подписка».",
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
    config_file = FSInputFile(f"configs/{filename}", filename=f"derox_vpn_{user.user_id}.json")
    
    await callback.message.answer_document(
        document=config_file,
        caption=f"🔑 <b>Ваш конфиг</b>\n\n"
                f"📦 Тариф: {user.tariff}\n"
                f"📅 Активен до: <b>{user.time_sub.strftime('%d.%m.%Y %H:%M')}</b>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()
