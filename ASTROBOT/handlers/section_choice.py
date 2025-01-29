from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Text

router = Router()

@router.message(Text(equals=["Подписка"], ignore_case=True))
async def subscription_choice(message: Message):
    """Пользователь выбрал 'Подписка'."""
    await message.answer(
        "Раздел 'Подписка'.\n"
        "Команды:\n"
        " - /subscribe (активация подписки)\n"
        " - /unsubscribe (деактивация)\n"
        " - /status (проверка статуса)\n"
    )
