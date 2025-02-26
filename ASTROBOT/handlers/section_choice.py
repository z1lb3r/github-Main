"""
Обработчики для выбора разделов бота через клавиатуру.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(lambda msg: msg.text and msg.text.lower() == "подписка")
async def subscription_choice(message: Message):
    """
    Обработчик выбора раздела "Подписка".
    
    Args:
        message (Message): Сообщение Telegram
    """
    await message.answer(
        "Раздел 'Подписка'.\n"
        "Команды:\n"
        " - /subscribe (активация)\n"
        " - /unsubscribe (деактивация)\n"
        " - /status (проверка статуса)\n"
    )

@router.message(lambda msg: msg.text and msg.text.lower() == "гороскоп")
async def horoscope_choice(message: Message):
    """
    Обработчик выбора раздела "Гороскоп".
    
    Args:
        message (Message): Сообщение Telegram
    """
    # Заготовка: пока сообщаем, что раздел в разработке
    await message.answer("Раздел 'Гороскоп' пока в разработке.")
    
@router.message(lambda msg: msg.text and msg.text.lower() == "изменить данные")
async def change_data_choice(message: Message, state: FSMContext):
    """
    Обработчик выбора раздела "Изменить данные".
    Запускает процесс онбординга заново для изменения данных пользователя.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    # Для изменения данных повторно запускаем анкету
    await message.answer("Измените ваши данные. Введите ваше имя и фамилию:")
    from handlers import onboarding
    await onboarding.start_onboarding(message, state)