"""
Enhanced referral system implementation.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.db import get_referrals, get_total_referral_rewards, add_referral, activate_referral, add_to_balance
from config import REFERRAL_REWARD_USD
from .keyboards import get_back_to_menu_keyboard
from logger import handlers_logger as logger

# Correct bot username
BOT_USERNAME = "cz_astrobot_bot"  # Правильное имя бота

router = Router()

# Function to handle referral registration
def register_referral(user_id, ref_user_id):
    """
    Registers a new referral relationship.
    
    Args:
        user_id (int): ID of the new user
        ref_user_id (int): ID of the referrer
    """
    # Don't allow self-referrals
    if user_id == ref_user_id:
        logger.warning(f"Попытка самореферальства пользователем {user_id}")
        return False
    
    # Add referral to database
    logger.info(f"Регистрация реферальной связи: пользователь {user_id} пришел от реферера {ref_user_id}")
    add_referral(user_id, ref_user_id)
    return True

# Function to reward referrer when referral completes a target action
def reward_referrer(referrer_id, referred_id):
    """
    Rewards a referrer for bringing in a new user.
    
    Args:
        referrer_id (int): ID of the referrer
        referred_id (int): ID of the referred user
    """
    # Add reward to referrer's balance
    logger.info(f"Начисление реферального вознаграждения ({REFERRAL_REWARD_USD} баллов) пользователю {referrer_id} за привлечение пользователя {referred_id}")
    add_to_balance(
        referrer_id,
        REFERRAL_REWARD_USD,
        f"Реферальное вознаграждение за пользователя {referred_id}",
        "USD",
        REFERRAL_REWARD_USD
    )

# Enhanced function to show referral program details
async def show_referral_program_enhanced(message: Message):
    """
    Shows information about the referral program with enhanced details.
    """
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} запросил информацию о реферальной программе")
    
    # Формируем реферальную ссылку с правильным username бота
    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    
    # Get referral statistics
    referrals = get_referrals(user_id)
    total_rewards = get_total_referral_rewards(user_id)
    active_referrals = sum(1 for ref in referrals if ref['status'] == 'active')
    pending_referrals = sum(1 for ref in referrals if ref['status'] == 'pending')
    
    logger.debug(f"Статистика рефералов для {user_id}: активных={active_referrals}, ожидающих={pending_referrals}, всего заработано=${total_rewards:.2f}")
    
    await message.answer(
        f"👥 Реферальная программа\n\n"
        f"Приглашайте друзей и получайте вознаграждение!\n\n"
        f"• Вы получаете ${REFERRAL_REWARD_USD:.2f} за каждого нового пользователя, который присоединится по вашей ссылке\n"
        f"• Нет ограничений на количество рефералов\n"
        f"• Вознаграждение зачисляется прямо на ваш баланс\n\n"
        f"📊 Ваша статистика:\n"
        f"• Активных рефералов: {active_referrals}\n"
        f"• Ожидающих рефералов: {pending_referrals}\n"
        f"• Общий заработок: ${total_rewards:.2f}\n\n"
        f"🔗 Ваша реферальная ссылка:\n{ref_link}",
        reply_markup=get_referral_keyboard(ref_link)
    )

# Function to get referral keyboard
def get_referral_keyboard(ref_link: str):
    """
    Creates a keyboard for the referral program.
    
    Args:
        ref_link (str): Referral link to copy
    
    Returns:
        InlineKeyboardMarkup: Keyboard with referral options
    """
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🔗 Скопировать реферальную ссылку", callback_data="copy_ref_link")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика приглашений", callback_data="ref_stats")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main_menu")
    )
    return builder.as_markup()

# Enhanced callback query handler for referral statistics
async def show_ref_stats_enhanced(callback: CallbackQuery):
    """
    Shows detailed referral statistics.
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} запросил статистику своих рефералов")
    
    referrals = get_referrals(user_id)
    total_rewards = get_total_referral_rewards(user_id)
    
    if not referrals:
        logger.debug(f"У пользователя {user_id} нет рефералов")
        await callback.message.answer(
            "📊 Статистика реферальной программы\n\n"
            "Вы ещё никого не пригласили.\n"
            "Поделитесь своей реферальной ссылкой, чтобы начать зарабатывать!",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    # Prepare detailed statistics message
    msg = "📊 Подробная статистика рефералов\n\n"
    
    # Active referrals
    active_refs = [ref for ref in referrals if ref['status'] == 'active']
    if active_refs:
        msg += "✅ Активные рефералы:\n"
        for i, ref in enumerate(active_refs, 1):
            name = ref['full_name'] or f"Пользователь #{ref['user_id']}"
            date = ref['activated_at']
            reward = ref['reward_amount']
            msg += f"{i}. {name} - ${reward:.2f} (активирован {date})\n"
        msg += "\n"
    
    # Pending referrals
    pending_refs = [ref for ref in referrals if ref['status'] == 'pending']
    if pending_refs:
        msg += "⏳ Ожидающие рефералы:\n"
        for i, ref in enumerate(pending_refs, 1):
            name = ref['full_name'] or f"Пользователь #{ref['user_id']}"
            date = ref['created_at']
            msg += f"{i}. {name} (присоединился {date})\n"
        msg += "\n"
    
    msg += f"💰 Общий заработок: ${total_rewards:.2f}"
    
    logger.debug(f"Отправка детальной статистики рефералов для пользователя {user_id}")
    await callback.message.answer(
        msg,
        reply_markup=get_back_to_menu_keyboard()
    )

# Register router handlers
@router.message(F.text == "👥 Реферальная программа")
async def handle_referral_menu(message: Message):
    """
    Handler for the "Referral Program" button.
    """
    await show_referral_program_enhanced(message)

@router.callback_query(F.data == "ref_stats")
async def handle_ref_stats(callback: CallbackQuery):
    """
    Handler for referral statistics button.
    """
    await show_ref_stats_enhanced(callback)

@router.callback_query(F.data == "copy_ref_link")
async def handle_copy_ref_link(callback: CallbackQuery):
    """
    Handler for copy referral link button.
    """
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} скопировал реферальную ссылку")
    
    # Формируем реферальную ссылку с правильным username бота
    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    
    await callback.answer("Ссылка скопирована!")
    await callback.message.answer(
        f"Ваша реферальная ссылка:\n{ref_link}\n\n"
        "Ссылка скопирована в буфер обмена."
    )