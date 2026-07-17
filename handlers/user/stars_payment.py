from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from db.models import Users

router = Router()

# Цены за тарифы (в Telegram Stars)
PRICES = {
    "month": 100,
    "sixmonth": 500,
    "year": 1000
}

# Длительность тарифов (в днях)
DURATIONS = {
    "month": 30,
    "sixmonth": 180,
    "year": 365
}


@router.callback_query(lambda c: c.data == "free_trial")
async def free_trial_handler(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    
    # Проверяем, есть ли уже подписка
    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    
    if user and user.time_sub and user.time_sub > datetime.now():
        await callback.message.answer("❌ У вас уже есть активная подписка!")
        await callback.answer()
        return
    
    # Проверяем, не использовал ли уже пробный период
    if user and user.trial_used:
        await callback.message.answer("❌ Вы уже использовали пробный период!")
        await callback.answer()
        return
    
    # Активируем пробный период на 3 дня
    if not user:
        user = Users(user_id=user_id, fullname=callback.from_user.full_name)
        session.add(user)
    
    user.time_sub = datetime.now() + timedelta(days=3)
    user.tariff = "Пробный (3 дня)"
    user.trial_used = True
    
    await session.commit()
    
    await callback.message.answer(
        "🎉 <b>Пробный период активирован!</b>\n\n"
        "✅ Доступ открыт на <b>3 дня</b>\n"
        "⚠️ После окончания пробного периода подписка отключится автоматически.\n\n"
        "Чтобы продлить доступ, выберите тариф в меню «Подписка».",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("tariff_"))
async def tariff_callback(callback: CallbackQuery):
    tariff_key = callback.data.replace("tariff_", "")
    
    if tariff_key not in PRICES:
        await callback.answer("Неверный тариф")
        return
    
    price = PRICES[tariff_key]
    duration = DURATIONS[tariff_key]
    
    # Названия тарифов для отображения
    tariff_names = {
        "month": "1 месяц",
        "sixmonth": "6 месяцев",
        "year": "1 год"
    }
    
    # Отправляем инвойс для оплаты Stars
    await callback.message.answer_invoice(
        title=f"DeroX VPN — {tariff_names[tariff_key]}",
        description=f"Доступ к VPN на {duration} дней",
        payload=tariff_key,  # Передаём ключ тарифа
        provider_token="",
        currency="XTR",  # Telegram Stars
        prices=[
            LabeledPrice(label=tariff_names[tariff_key], amount=price)
        ],
        start_parameter="derox_vpn_subscription"
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout: PreCheckoutQuery):
    # Всегда подтверждаем оплату
    await pre_checkout.answer(ok=True)


@router.message(lambda message: message.successful_payment)
async def successful_payment_handler(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    payment_info = message.successful_payment
    
    tariff_key = payment_info.invoice_payload
    duration = DURATIONS.get(tariff_key, 30)
    
    tariff_names = {
        "month": "1 месяц",
        "sixmonth": "6 месяцев",
        "year": "1 год"
    }
    
    # Обновляем подписку пользователя
    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    
    if not user:
        user = Users(user_id=user_id, fullname=message.from_user.full_name)
        session.add(user)
    
    # Если уже есть подписка — продлеваем
    if user.time_sub and user.time_sub > datetime.now():
        user.time_sub = user.time_sub + timedelta(days=duration)
    else:
        user.time_sub = datetime.now() + timedelta(days=duration)
    
    user.tariff = tariff_names.get(tariff_key, tariff_key)
    
    await session.commit()
    
    await message.answer(
        f"✅ <b>Оплата прошла успешно!</b>\n\n"
        f"📦 Тариф: {tariff_names.get(tariff_key, tariff_key)}\n"
        f"📅 Подписка активна до: <b>{user.time_sub.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
        "Спасибо за покупку! 🎉",
        parse_mode=ParseMode.HTML
    )
