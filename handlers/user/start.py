from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Users, Stats
from filters.is_private import PrivateChatFilter

router = Router()


# Функция для создания главного меню (кнопки внизу экрана)
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
<b>DeroX VPN</b> - твой безопасный и быстрый доступ к интернету.

🌍 Безлимитный трафик
🔒 Анонимность и защита
⚡ Высокая скорость

Просто нажми START ⚡
    """

    await message.reply(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await message.answer("Меню:", reply_markup=get_main_menu())


# ============================================
# ОБРАБОТЧИКИ КНОПОК МЕНЮ
# ============================================

@router.message(lambda message: message.text == "👤 Профиль")
async def profile_handler(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    name = message.from_user.full_name
    
    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    
    if user and user.time_sub:
        sub_status = f"✅ Активна до: {user.time_sub.strftime('%d.%m.%Y %H:%M')}"
        tariff_info = f"Тариф: {user.tariff or 'Не указан'}"
    else:
        sub_status = "❌ У вас нет оформленной подписки."
        tariff_info = ""
    
    text = f"""
<b>👤 Профиль:</b>
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
<b>📦 Выберите тариф DeroX VPN:</b>

🔹 1 месяц — 100 ⭐
🔹 6 месяцев — 500 ⭐
🔹 1 год — 1000 ⭐

Оплата через Telegram Stars.
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 месяц — 100 ⭐", callback_data="tariff_month")],
            [InlineKeyboardButton(text="6 месяцев — 500 ⭐", callback_data="tariff_sixmonth")],
            [InlineKeyboardButton(text="1 год — 1000 ⭐", callback_data="tariff_year")]
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.message(lambda message: message.text == "👥 Пригласить")
async def invite_handler(message: Message):
    text = """
👥 <b>Пригласительная система DeroX VPN</b>

Приглашай друзей и получай бонусы!

Скоро здесь появится реферальная программа.
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

По всем вопросам обращайтесь в поддержку.
    """
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(lambda message: message.text == "🆘 Поддержка")
async def support_handler(message: Message):
    text = """
🆘 <b>Поддержка DeroX VPN</b>

По всем вопросам пишите: @support_username

Или оставьте сообщение, и мы ответим вам в ближайшее время.
    """
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(lambda message: message.text == "💳 CARDS")
async def cards_handler(message: Message):
    text = """
💳 <b>CARDS</b>

Здесь будут ваши карты и способы оплаты.

Функция в разработке.
    """
    await message.answer(text, parse_mode=ParseMode.HTML)
