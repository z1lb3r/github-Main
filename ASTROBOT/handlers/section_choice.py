from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message(lambda msg: msg.text and msg.text.lower() == "подписка")
async def subscription_choice(message: Message):
    await message.answer(
        "Раздел 'Подписка'.\n"
        "Команды:\n"
        " - /subscribe (активация)\n"
        " - /unsubscribe (деактивация)\n"
        " - /status (проверка статуса)\n"
    )

@router.message(lambda msg: msg.text and msg.text.lower() == "гороскоп")
async def horoscope_choice(message: Message):
    # Заготовка: пока никаких действий
    await message.answer("Раздел 'Гороскоп' пока в разработке.")
    
@router.message(lambda msg: msg.text and msg.text.lower() == "изменить данные")
async def change_data_choice(message: Message, state):
    # Для изменения данных повторно запускаем анкету
    await message.answer("Измените ваши данные. Введите ваше имя и фамилию:")
    from handlers import onboarding
    await onboarding.start_onboarding(message, state)
