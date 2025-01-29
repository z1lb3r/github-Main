from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message(lambda msg: msg.text and msg.text.lower() == "подписка")
async def subscription_choice(message: Message):
    """Пользователь выбрал 'Подписка' (через кнопку или вручную)."""
    await message.answer(
        "Раздел 'Подписка'.\n"
        "Команды:\n"
        " - /subscribe (активация)\n"
        " - /unsubscribe (деактивация)\n"
        " - /status (проверка статуса)\n"
    )