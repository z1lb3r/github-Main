"""
Обработчики для выбора разделов бота через клавиатуру.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from handlers.payment import get_payment_keyboard
from services.db import user_has_active_subscription

router = Router()

@router.message(lambda msg: msg.text and msg.text.lower() == "подписка")
async def subscription_choice(message: Message):
    """
    Обработчик выбора раздела "Подписка".
    
    Args:
        message (Message): Сообщение Telegram
    """
    # Проверяем статус подписки
    has_subscription = user_has_active_subscription(message.from_user.id)
    
    if has_subscription:
        await message.answer(
            "У вас активна подписка! Спасибо за поддержку.\n\n"
            "Команды управления подпиской:\n"
            " - /status (проверка статуса)\n"
            " - /unsubscribe (деактивация)\n"
        )
    else:
        await message.answer(
            "У вас нет активной подписки.\n\n"
            "Оформите подписку, чтобы получить доступ ко всем функциям бота. "
            "Нажмите кнопку ниже для оплаты:",
            reply_markup=get_payment_keyboard()
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