import secrets
import string
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
# ГЕНЕРАЦИЯ КОДА (ключа активации)
# ============================================
def generate_activation_code(length: int = 12) -> str:
    """Генерирует уникальный код активации"""
    alphabet = string.ascii_uppercase + string.digits
    # Исключаем похожие символы: 0, O, I, 1
    alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def format_activation_code(code: str) -> str:
    """Форматирует код для удобного чтения (XXXX-XXXX-XXXX)"""
    chunks = [code[i:i+4] for i in range(0, len(code), 4)]
    return '-'.join(chunks)


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
    
    # Генерируем код активации
    raw_code = generate_activation_code(12)
    formatted_code = format_activation_code(raw_code)
    
    # Активируем пробный период на 3 дня
    if not user:
        user = Users(user_id=user_id, fullname=callback.from_user.full_name)
        session.add(user)
    
    user.time_sub = datetime.now() + timedelta(days=3)
    user.tariff = "Пробный (3 дня)"
    user.trial_used = True
    user.link = raw_code  # Сохраняем код в базу
    
    await session.commit()
    
    await callback.message.answer(
        f"🎉 <b>Пробный период активирован!</b>\n\n"
        f"✅ Доступ открыт на <b>3 дня</b>\n"
        f"📅 Активен до: <b>{(datetime.now() + timedelta(days=3)).strftime('%d.%m.%Y %H:%M')}</b>\n\n"
        f"🔑 <b>Ваш код активации:</b>\n"
        f"<code>{formatted_code}</code>\n\n"
        f"⚠️ Сохраните этот код! Он понадобится для входа в сервис.\n"
        f"⚠️ После окончания пробного периода подписка отключится автоматически.",
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
    parts = payload.split('_')
    if len(parts) >= 3:
        tariff_name = parts[2]
    else:
        tariff_name = "month"
    
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
        user.time_sub = tariff.get_expiration_date(user.time_sub)
    else:
        user.time_sub = tariff.get_expiration_date(datetime.now())
    
    user.tariff = tariff.name
    
    # Генерируем новый код при каждой оплате
    raw_code = generate_activation_code(12)
    formatted_code = format_activation_code(raw_code)
    user.link = raw_code
    
    await session.commit()
    
    # Определяем количество дней
    days_map = {
        "🌙 Месяц": 31,
        "🌕 6 месяцев": 186,
        "🌚 1 год": 365
    }
    days = days_map.get(tariff.name, 31)
    
    await message.answer(
        f"✅ <b>Оплата прошла успешно!</b>\n\n"
        f"📦 Тариф: {tariff.name}\n"
        f"📅 Подписка активна до: <b>{user.time_sub.strftime('%d.%m.%Y %H:%M')}</b>\n"
        f"⏳ Длительность: <b>{days} дней</b>\n\n"
        f"🔑 <b>Ваш код активации:</b>\n"
        f"<code>{formatted_code}</code>\n\n"
        f"⚠️ Сохраните этот код! Он понадобится для входа в сервис.",
        parse_mode=ParseMode.HTML
    )


# ============================================
# ПОЛУЧИТЬ КОД (для уже оплативших)
# ============================================
@router.callback_query(lambda c: c.data == "get_code")
async def get_code_handler(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    
    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    
    if not user or not user.link:
        await callback.message.answer(
            "❌ У вас нет активного кода.\n\n"
            "Оформите подписку в меню «Подписка».",
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        return
    
    formatted_code = format_activation_code(user.link)
    
    await callback.message.answer(
        f"🔑 <b>Ваш код активации:</b>\n"
        f"<code>{formatted_code}</code>\n\n"
        f"📅 Подписка активна до: <b>{user.time_sub.strftime('%d.%m.%Y %H:%M') if user.time_sub else 'Не указано'}</b>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()
