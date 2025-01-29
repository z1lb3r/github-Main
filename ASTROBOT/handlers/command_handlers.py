from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from .keyboards import main_menu_kb
from services.db import (
    add_user_if_not_exists,
    activate_subscription,
    deactivate_subscription,
    user_has_active_subscription
)

router = Router()

@router.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    """Запуск бота: создаём пользователя, приветствие + кнопки."""
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    add_user_if_not_exists(user_id, username)

    await message.answer(
        "Привет! Я — твой эзотерический помощник.\n"
        "Выберите раздел:\n"
        "- Подписка\n"
        "- Расчёт композита\n"
        "- Расчёт Dream Rave\n\n"
        "Или используйте команды:\n"
        "/subscribe, /unsubscribe (подписка)\n"
        "/status (проверка статуса)\n",
        reply_markup=main_menu_kb
    )

@router.message(Command(commands=["subscribe"]))
async def cmd_subscribe(message: Message):
    """Активируем подписку."""
    user_id = message.from_user.id
    activate_subscription(user_id)
    await message.answer("Подписка активирована! Теперь у вас есть доступ ко всем функциям.")

@router.message(Command(commands=["unsubscribe"]))
async def cmd_unsubscribe(message: Message):
    """Отключаем подписку."""
    user_id = message.from_user.id
    deactivate_subscription(user_id)
    await message.answer("Подписка отменена. Если захотите, можете снова оформить /subscribe.")

@router.message(Command(commands=["status"]))
async def cmd_status(message: Message):
    """Проверка статуса подписки."""
    user_id = message.from_user.id
    status_text = "активна" if user_has_active_subscription(user_id) else "не активна"
    await message.answer(f"Ваша подписка сейчас {status_text}.")