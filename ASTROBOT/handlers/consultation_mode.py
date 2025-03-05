"""
Consultation mode system implementation.
This allows the bot to track whether a user is in consultation mode
and only charge the balance during consultations.
"""

import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import MIN_REQUIRED_BALANCE
from services.db import get_user_balance

router = Router()

# Function to start consultation mode
async def start_consultation_mode(user_id: int, state: FSMContext):
    """
    Starts the consultation mode for a user.
    
    Args:
        user_id (int): ID of the user
        state (FSMContext): FSM context
    """
    # Set consultation mode flag in state
    await state.update_data(in_consultation=True)
    await state.update_data(consultation_start_time=time.time())
    
    # Clear previous conversation history if any
    await state.update_data(conversation_history="")
    
    print(f"User {user_id} started consultation mode")

# Function to end consultation mode
async def end_consultation_mode(user_id: int, state: FSMContext):
    """
    Ends the consultation mode for a user.
    
    Args:
        user_id (int): ID of the user
        state (FSMContext): FSM context
    """
    # Get current state data
    data = await state.get_data()
    
    # Calculate consultation duration
    start_time = data.get("consultation_start_time", 0)
    duration = time.time() - start_time if start_time else 0
    
    # Reset consultation mode flag
    await state.update_data(in_consultation=False)
    await state.update_data(consultation_start_time=None)
    
    print(f"User {user_id} ended consultation mode. Duration: {duration:.2f} seconds")
    
    return duration

# Function to check if user is in consultation mode
async def is_in_consultation(state: FSMContext) -> bool:
    """
    Checks if a user is currently in consultation mode.
    
    Args:
        state (FSMContext): FSM context
        
    Returns:
        bool: True if user is in consultation mode, False otherwise
    """
    data = await state.get_data()
    is_active = data.get("in_consultation", False)
    print(f"Проверка режима консультации: {is_active}")
    return is_active

# Function to generate end consultation keyboard
def get_end_consultation_keyboard():
    """
    Creates a keyboard with an 'End Consultation' button.
    
    Returns:
        InlineKeyboardMarkup: Keyboard with end consultation button
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⛔ Завершить консультацию",
        callback_data="end_consultation"
    )
    return builder.as_markup()

# Function to handle consultation start
async def handle_consultation_start(callback: CallbackQuery, state: FSMContext):
    """
    Handler for starting a consultation.
    
    Args:
        callback (CallbackQuery): Callback query
        state (FSMContext): FSM context
    """
    from .keyboards import main_menu_kb
    
    user_id = callback.from_user.id
    balance = get_user_balance(user_id)
    
    # Отладочный вывод
    print(f"Запуск консультации: user_id={user_id}, баланс={balance:.0f} баллов, минимум={MIN_REQUIRED_BALANCE:.0f} баллов")
    
    # Check if user has enough balance
    if balance < MIN_REQUIRED_BALANCE:
        await callback.message.answer(
            f"⚠️ Недостаточно средств для консультации.\n\n"
            f"Ваш текущий баланс: {balance:.0f} баллов\n"
            f"Минимальный баланс: {MIN_REQUIRED_BALANCE:.0f} баллов\n\n"
            f"Пожалуйста, пополните баланс.",
            reply_markup=main_menu_kb
        )
        return
    
    # Start consultation mode
    await start_consultation_mode(user_id, state)
    
    await callback.message.answer(
        "🔮 Консультация начата!\n\n"
        "Теперь вы можете задавать любые вопросы о вашем анализе Human Design. "
        "Баланс будет расходоваться только в режиме консультации.\n\n"
        "Когда закончите, нажмите кнопку 'Завершить консультацию'.",
        reply_markup=get_end_consultation_keyboard()
    )

# Function to handle consultation end
async def handle_consultation_end(callback: CallbackQuery, state: FSMContext):
    """
    Handler for ending a consultation.
    
    Args:
        callback (CallbackQuery): Callback query
        state (FSMContext): FSM context
    """
    from .keyboards import main_menu_kb
    from .change_data import get_updated_main_menu_keyboard  # Добавляем импорт
    
    user_id = callback.from_user.id
    
    # End consultation mode and get duration
    duration = await end_consultation_mode(user_id, state)
    
    # Get current balance
    balance = get_user_balance(user_id)
    print(f"Завершение консультации: user_id={user_id}, текущий баланс={balance:.0f} баллов")
    
    # Calculate minutes and seconds
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    
    await callback.message.answer(
        f"✅ Консультация завершена!\n\n"
        f"Продолжительность: {minutes} мин. {seconds} сек.\n"
        f"Текущий баланс: {balance:.0f} баллов\n\n"
        f"Спасибо за использование нашего сервиса. Вы можете начать новую консультацию в любое время.",
        reply_markup=get_updated_main_menu_keyboard()  # Используем обновленную клавиатуру
    )

# Register callback handlers
@router.callback_query(F.data == "start_consultation")
async def consultation_start_handler(callback: CallbackQuery, state: FSMContext):
    """
    Handler for starting a consultation from callback query.
    """
    await callback.answer()
    await handle_consultation_start(callback, state)

@router.callback_query(F.data == "end_consultation")
async def consultation_end_handler(callback: CallbackQuery, state: FSMContext):
    """
    Handler for ending a consultation from callback query.
    """
    await callback.answer()
    await handle_consultation_end(callback, state)