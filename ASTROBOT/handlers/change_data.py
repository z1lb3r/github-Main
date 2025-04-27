"""
Implementation for the "Change my data" button
and related functionality.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from services.db import get_user_profile
from logger import handlers_logger as logger

router = Router()

def get_updated_main_menu_keyboard():
    """
    Returns an updated main menu keyboard with the "Change my data" option.
    """
    logger.debug("Создание обновленной клавиатуры главного меню")
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="⭐️🔄⭐️ БЕСПЛАТНО проверить совместимость")
            ],
            [
                KeyboardButton(text="✨ Начать консультацию"),
                KeyboardButton(text="🔄 Продолжить консультацию")
            ],
            [
                KeyboardButton(text="💰 Баланс"),
                KeyboardButton(text="👤 Изменить мои данные")
            ],
            [
                KeyboardButton(text="📋 Пользовательское соглашение"),
                KeyboardButton(text="👥 Реферальная программа")
            ],
            [
                KeyboardButton(text="ℹ️ О нас"),
                KeyboardButton(text="📞 Контакты")
            ]
        ],
        resize_keyboard=True
    )

# Handler for "Change My Data" button
@router.message(F.text == "👤 Изменить мои данные")
async def change_user_data(message: Message, state: FSMContext):
    """
    Handler for the "Change My Data" button.
    Starts the onboarding process again to change user data.
    
    Args:
        message (Message): Telegram message
        state (FSMContext): FSM context
    """
    # Get current user profile
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} запросил изменение своих данных")
    
    profile = get_user_profile(user_id)
    
    # Show current data to user
    if profile:
        logger.debug(f"Показ текущих данных пользователя {user_id}")
        current_data = (
            "Ваши текущие данные:\n\n"
            f"Имя: {profile.get('full_name', 'Не указано')}\n"
            f"Дата рождения: {profile.get('birth_date', 'Не указана')}\n"
            f"Время рождения: {profile.get('birth_time', 'Не указано')}\n"
            f"Место рождения: {profile.get('latitude', 'Не указано')}, "
            f"{profile.get('longitude', 'Не указано')}\n\n"
            "Пожалуйста, введите ваши новые данные. Начнем с вашего имени:"
        )
    else:
        logger.warning(f"Профиль пользователя {user_id} не найден")
        current_data = "У вас пока нет данных профиля. Давайте их заполним."
    
    await message.answer(current_data)
    
    # Start onboarding process from the beginning
    from handlers.onboarding import OnboardingStates
    await state.set_state(OnboardingStates.waiting_for_name)
    logger.debug(f"Установлено состояние 'waiting_for_name' для пользователя {user_id}")

# Function to restart onboarding process
async def restart_onboarding(message: Message, state: FSMContext):
    """
    Restarts the onboarding process for a user who wants to change their data.
    Args:
        message (Message): Telegram message
        state (FSMContext): FSM context
    """
    user_id = message.from_user.id
    logger.info(f"Перезапуск процесса онбординга для пользователя {user_id}")
    
    # Set state to waiting for name
    from handlers.onboarding import OnboardingStates
    await state.set_state(OnboardingStates.waiting_for_name)
    logger.debug(f"Установлено состояние 'waiting_for_name' для пользователя {user_id}")
    
    # Start onboarding with the first step
    await message.answer(
        "Давайте обновим информацию вашего профиля.\n\n"
        "Пожалуйста, введите ваше полное имя:"
    )

# Add router handler for edit_profile callback
@router.callback_query(F.data == "edit_profile")
async def edit_profile_handler(callback: CallbackQuery, state: FSMContext):
    """
    Handler for edit profile button from callback query.
    """
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} запросил редактирование профиля через callback")
    
    await callback.answer()
    await restart_onboarding(callback.message, state)