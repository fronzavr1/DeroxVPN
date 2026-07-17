@staticmethod
async def send_payment_message(cq: CallbackQuery, tariff: Tariff):
    """Отправляет сообщение с информацией об оплате выбранного тарифа"""
    await cq.message.answer_invoice(
        title=f'Подписка: {tariff.name}',
        description=f'Доступ к приватному каналу на {tariff.duration}',
        prices=[LabeledPrice(label="XTR", amount=tariff.price)],
        provider_token='',
        currency='XTR',
        payload=f"sub_{cq.from_user.id}_{cq.data.split('_')[2]}"
    )
    await cq.answer()  # <-- ДОБАВЬ ЭТУ СТРОКУ
