"""
Обработчики команд Telegram-бота.
Обрабатывает команды /start, /subscribe, /unsubscribe, /status, /payment.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from handlers.onboarding import start_onboarding
from handlers.payment import get_payment_keyboard

from .keyboards import main_menu_kb
from services.db import (
    add_user_if_not_exists,
    activate_subscription,
    deactivate_subscription,
    user_has_active_subscription,
    get_user_profile
)

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start.
    Регистрирует пользователя и предлагает пройти онбординг, если профиль не заполнен.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    
    # Добавляем пользователя в БД, если его там еще нет
    add_user_if_not_exists(user_id, username)
    
    # Получаем профиль пользователя
    profile = get_user_profile(user_id)
    
    if not profile:
        # Если профиль не заполнен, запускаем анкетирование
        await message.answer("Для начала работы необходимо заполнить анкету.")
        await start_onboarding(message, state)
    else:
        # Если профиль заполнен, показываем главное меню
        await message.answer(
            f"Привет, {profile.get('full_name')}! Выберите раздел:\n"
            "- Подписка\n"
            "- Хьюман дизайн\n"
            "- Гороскоп\n"
            "- Изменить данные\n\n"
            "Или используйте команды:\n"
            "/subscribe, /unsubscribe (подписка)\n"
            "/status (проверка статуса)\n"
            "/payment (оплата подписки)",
            reply_markup=main_menu_kb
        )

@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    """
    Обработчик команды /subscribe.
    Предлагает пользователю оплатить подписку, если она еще не активирована.
    
    Args:
        message (Message): Сообщение Telegram
    """
    # Проверяем, есть ли уже активная подписка
    if user_has_active_subscription(message.from_user.id):
        await message.answer("У вас уже есть активная подписка.")
        return
    
    # Предлагаем оплатить подписку через CrystalPay
    await message.answer(
        "Для активации подписки, пожалуйста, оплатите ее. "
        "Вы можете сделать это через команду /payment.",
        reply_markup=get_payment_keyboard()
    )

@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message):
    """
    Обработчик команды /unsubscribe.
    Деактивирует подписку пользователя.
    
    Args:
        message (Message): Сообщение Telegram
    """
    deactivate_subscription(message.from_user.id)
    await message.answer("Подписка отменена. Если захотите, можете снова оформить /subscribe.")

@router.message(Command("status"))
async def cmd_status(message: Message):
    """
    Обработчик команды /status.
    Показывает статус подписки пользователя.
    
    Args:
        message (Message): Сообщение Telegram
    """
    status = "активна" if user_has_active_subscription(message.from_user.id) else "не активна"
    await message.answer(f"Ваша подписка сейчас {status}.")

@router.message(Command("pay"))
async def cmd_pay(message: Message):
    """
    Обработчик команды /pay.
    Альтернативная команда для /payment.
    
    Args:
        message (Message): Сообщение Telegram
    """
    # Перенаправляем на обработчик /payment
    from handlers.payment import cmd_payment
    await cmd_payment(message)