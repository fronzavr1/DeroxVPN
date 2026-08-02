from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from db.models import Users, Stats
from filters.is_private import PrivateChatFilter

router = Router()

# 👇 ТВОЙ ЮЗЕРНЕЙМ (без @)
ADMIN_USERNAME = "DeroXHelper"


def get_days_for_tariff(tariff_name: str) -> int:
    """Возвращает количество дней для тарифа"""
    if not tariff_name:
        return 30
    if "Пробный" in tariff_name or "3 дня" in tariff_name:
        return 3
    elif "Месяц" in tariff_name or "месяц" in tariff_name:
        return 31
    elif "6 месяцев" in tariff_name or "6 мес" in tariff_name:
        return 186
    elif "Год" in tariff_name or "год" in tariff_name:
        return 365
    else:
        return 30


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="📦 Подписка")],
            [KeyboardButton(text="👥 Пригласить"), KeyboardButton(text="📜 Правила")],
            [KeyboardButton(text="🆘 Поддержка"), KeyboardButton(text="💳 CARDS")]
        ],
        resize_keyboard=True
    )


@router.message(PrivateChatFilter(), CommandStart())
async def start(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    fullname = message.from_user.full_name

    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    if not user:
        user = Users(user_id=user_id, fullname=fullname)
        session.add(user)
        await session.commit()

    stats = (await session.execute(select(Stats).where(Stats.id == 1))).scalar_one_or_none()
    if not stats:
        stats = Stats()
        session.add(stats)
        await session.commit()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🚀 ПОПРОБОВАТЬ БЕСПЛАТНО', callback_data='free_trial')]
        ]
    )

    text = """
<b>DeroX VPN</b> — твой безопасный и быстрый доступ к интернету.

🌍 Безлимитный трафик
🔒 Анонимность и защита
⚡ Высокая скорость

Просто нажми START ⚡
    """

    await message.reply(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await message.answer("Выберите действие:", reply_markup=get_main_menu())


# ============================================
# ОБРАБОТЧИКИ КНОПОК ГЛАВНОГО МЕНЮ
# ============================================

@router.message(lambda message: message.text == "👤 Профиль")
async def profile_handler(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    username = message.from_user.username
    name = message.from_user.full_name
    
    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    
    now = datetime.now()
    
    # Если это админ
    if username and username.lower() == ADMIN_USERNAME.lower():
        sub_status = "👑 Администратор"
        tariff_info = "📦 Тариф: Админский доступ"
        if user and user.time_sub:
            sub_status = f"👑 Активен до: {user.time_sub.strftime('%d.%m.%Y %H:%M')}"
        
        text = f"""
<b>👤 Профиль</b>
ID: {user_id}
Имя: {name}

<b>📅 Подписка:</b>
{sub_status}
{tariff_info}

🔑 Вы — администратор бота.
        """
        await message.answer(text, parse_mode=ParseMode.HTML)
        return
    
    # Обычный пользователь
    if user and user.time_sub and user.time_sub > now:
        sub_status = f"✅ Активна до: {user.time_sub.strftime('%d.%m.%Y %H:%M')}"
        tariff_info = f"📦 Тариф: {user.tariff or 'Не указан'}"
    else:
        sub_status = "❌ У вас нет активной подписки"
        tariff_info = ""
    
    text = f"""
<b>👤 Профиль</b>
ID: {user_id}
Имя: {name}

<b>📅 Подписка:</b>
{sub_status}
{tariff_info}

> Для покупки доступа перейдите в меню «Подписка».
    """
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(lambda message: message.text == "📦 Подписка")
async def subscription_handler(message: Message):
    text = """
<b>💡 Выберите тариф:</b>

🎁 <b>Пробный период</b> — 3 дня (бесплатно, 1 раз)
🌙 <b>1 месяц</b> — 100 ⭐
🌕 <b>6 месяцев</b> — 500 ⭐
🌚 <b>1 год</b> — 1000 ⭐

Оплата через Telegram Stars.
    """
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Пробный период (3 дня)", callback_data="free_trial")],
            [InlineKeyboardButton(text="🌙 1 месяц — 100 ⭐", callback_data="tariff_month")],
            [InlineKeyboardButton(text="🌕 6 месяцев — 500 ⭐", callback_data="tariff_sixmonth")],
            [InlineKeyboardButton(text="🌚 1 год — 1000 ⭐", callback_data="tariff_year")]
        ]
    )
    
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.message(lambda message: message.text == "👥 Пригласить")
async def invite_handler(message: Message):
    text = f"""
👥 <b>Пригласительная система</b>

Приглашай друзей и получай бонусы!

🔗 Твоя реферальная ссылка:
<code>https://t.me/DeroXVPN_bot?start=ref_{message.from_user.id}</code>

Скоро здесь появится полноценная реферальная программа.
    """
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(lambda message: message.text == "📜 Правила")
async def rules_handler(message: Message):
    text = """
📜 <b>Правила пользования DeroX VPN</b>

1. Подписка даёт доступ к VPN на выбранный период
2. Доступ автоматически продлевается при оплате
3. При нарушении правил доступ может быть заблокирован
4. Возврат средств не производится
5. Запрещено использовать VPN для незаконных действий

По всем вопросам обращайтесь в поддержку.
    """
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(lambda message: message.text == "🆘 Поддержка")
async def support_handler(message: Message):
    text = f"""
🆘 <b>Поддержка DeroX VPN</b>

По всем вопросам пишите нашему менеджеру:
👉 <b>@{ADMIN_USERNAME}</b>

Или нажмите кнопку ниже, чтобы написать в поддержку.
    """
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📩 Написать в поддержку", url=f"https://t.me/{ADMIN_USERNAME}")],
            [InlineKeyboardButton(text="📖 Часто задаваемые вопросы", callback_data="faq")]
        ]
    )
    
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.message(lambda message: message.text == "💳 CARDS")
async def cards_handler(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    username = message.from_user.username
    
    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    
    now = datetime.now()
    
    # Если админ
    if username and username.lower() == ADMIN_USERNAME.lower():
        text = """
💳 <b>CARDS — Админ</b>

👑 Вы — администратор бота.
📅 Подписка: бессрочная (можно продлевать через пробный период)

🔄 Нажмите «Пробный период», чтобы обновить доступ.
        """
        await message.answer(text, parse_mode=ParseMode.HTML)
        return
    
    # Обычный пользователь
    if not user or not user.time_sub:
        text = """
💳 <b>CARDS</b>

❌ У вас нет активной подписки.

📌 Оформите подписку в меню «Подписка».
        """
        await message.answer(text, parse_mode=ParseMode.HTML)
        return
    
    if user.time_sub <= now:
        text = """
💳 <b>CARDS</b>

❌ Ваша подписка истекла.

📌 Продлите подписку в меню «Подписка».
        """
        await message.answer(text, parse_mode=ParseMode.HTML)
        return
    
    # Активная подписка
    days = get_days_for_tariff(user.tariff)
    start_date = user.time_sub - timedelta(days=days)
    end_date = user.time_sub
    days_left = (end_date - now).days
    
    text = f"""
💳 <b>CARDS</b>

📦 <b>Тариф:</b> {user.tariff or 'Не указан'}
📅 <b>Активна с:</b> {start_date.strftime('%d.%m.%Y')}
📅 <b>Активна до:</b> {end_date.strftime('%d.%m.%Y')}
⏳ <b>Осталось дней:</b> {days_left}

📌 Чтобы продлить подписку, перейдите в меню «Подписка».
    """
    await message.answer(text, parse_mode=ParseMode.HTML)


# ============================================
# ДОПОЛНИТЕЛЬНЫЕ ОБРАБОТЧИКИ
# ============================================

@router.callback_query(lambda c: c.data == "faq")
async def faq_handler(callback: types.CallbackQuery):
    text = """
📖 <b>Часто задаваемые вопросы</b>

❓ <b>Как активировать подписку?</b>
Оплатите тариф в меню «Подписка» и скачайте конфиг.

❓ <b>Что делать, если конфиг не работает?</b>
Напишите в поддержку — мы поможем.

❓ <b>Можно ли вернуть деньги?</b>
Возврат средств не производится.

❓ <b>Сколько устройств можно подключить?</b>
Один конфиг = одно устройство.
    """
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML)
    await callback.answer()
