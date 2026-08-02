@router.message(lambda message: message.text == "👤 Профиль")
async def profile_handler(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    username = message.from_user.username
    name = message.from_user.full_name
    
    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    
    now = datetime.now()
    
    # Если это админ — показываем вечную подписку
    if username and username.lower() == ADMIN_USERNAME.lower():
        sub_status = "👑 Вечный доступ (админ)"
        tariff_info = "📦 Тариф: Администратор"
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
