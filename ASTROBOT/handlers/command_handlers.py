from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from handlers.onboarding import start_onboarding

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
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    add_user_if_not_exists(user_id, username)
    profile = get_user_profile(user_id)
    if not profile:
        # Если профиль не заполнен, запускаем анкетирование
        await message.answer("Для начала работы необходимо заполнить анкету.")
        await start_onboarding(message, state)
    else:
        await message.answer(
            f"Привет, {profile.get('full_name')}! Выберите раздел:\n"
            "- Подписка\n"
            "- Хьюман дизайн\n"
            "- Гороскоп\n"
            "- Изменить данные\n\n"
            "Или используйте команды:\n"
            "/subscribe, /unsubscribe (подписка)\n"
            "/status (проверка статуса)\n",
            reply_markup=main_menu_kb
        )

@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    activate_subscription(message.from_user.id)
    await message.answer("Подписка активирована! Теперь у вас есть доступ ко всем функциям.")

@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message):
    deactivate_subscription(message.from_user.id)
    await message.answer("Подписка отменена. Если захотите, можете снова оформить /subscribe.")

@router.message(Command("status"))
async def cmd_status(message: Message):
    status = "активна" if user_has_active_subscription(message.from_user.id) else "не активна"
    await message.answer(f"Ваша подписка сейчас {status}.")
