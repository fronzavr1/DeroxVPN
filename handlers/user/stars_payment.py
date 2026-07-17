from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from db.models import Users
from handlers.user.tariff import tariff_manager

router = Router()


# ============================================
# ПРОБНЫЙ ПЕРИОД (3 дня, 1 раз)
# ============================================
@router.callback_query(lambda c: c.data == "free_trial")
async def free_trial_handler(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    
    # Проверяем пользователя
    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    
    # Проверяем, есть ли активная подписка
    if user and user.time_sub and user.time_sub > datetime.now():
        await callback.message.answer("❌ У вас уже есть активная подписка!")
        await callback.answer()
        return
    
    # Проверяем, не использовал ли уже пробный период
    if user and user.trial_used:
        await callback.message.answer("❌ Вы уже использовали пробный период!\n\nВыберите платный тариф в меню «Подписка».")
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
        f"📅 Активен до: <b>{(datetime.now() + timedelta(days=3)).strftime('%d.%m.%Y %H:%M')}</b>\n\n"
        "⚠️ После окончания пробного периода подписка отключится автоматически.\n\n"
        "Чтобы продлить доступ, выберите тариф в меню «Подписка».",
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
    
    # Получаем название тарифа из payload
    payload = payment_info.invoice_payload
    # payload имеет формат: sub_123456_month
    parts = payload.split('_')
    if len(parts) >= 3:
        tariff_name = parts[2]  # month, sixmonth, year
    else:
        tariff_name = "month"  # Значение по умолчанию
    
    # Получаем тариф из tariff_manager
    tariff = tariff_manager.get_tariff(tariff_name)
    if not tariff:
        await message.answer("❌ Ошибка: тариф не найден")
        return
    
    # Обновляем подписку пользователя
    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    
    if not user:
        user = Users(user_id=user_id, fullname=message.from_user.full_name)
        session.add(user)
    
    # Вычисляем дату окончания
    if user.time_sub and user.time_sub > datetime.now():
        # Если уже есть подписка — продлеваем от текущей даты
        user.time_sub = tariff.get_expiration_date(user.time_sub)
    else:
        # Иначе начинаем с текущего момента
        user.time_sub = tariff.get_expiration_date(datetime.now())
    
    user.tariff = tariff.name
    
    await session.commit()
    
    await message.answer(
        f"✅ <b>Оплата прошла успешно!</b>\n\n"
        f"📦 Тариф: {tariff.name}\n"
        f"📅 Подписка активна до: <b>{user.time_sub.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
        "Спасибо за покупку! 🎉",
        parse_mode=ParseMode.HTML
    )
