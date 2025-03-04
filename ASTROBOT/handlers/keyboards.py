"""
Клавиатуры для Telegram-бота с иконками.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Клавиатура главного меню
main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✨ Начать консультацию")
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
            KeyboardButton(text="ℹ️ О нас")
        ]
    ],
    resize_keyboard=True
)

# Клавиатура для раздела "Баланс"
def get_balance_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💵 Пополнить", callback_data="deposit_balance"),
        InlineKeyboardButton(text="💸 Вывести", callback_data="withdraw_balance")
    )
    builder.row(
        InlineKeyboardButton(text="📊 История операций", callback_data="transaction_history")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main_menu")
    )
    return builder.as_markup()

# Кнопка возврата в главное меню
def get_back_to_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main_menu")
    )
    return builder.as_markup()

# Клавиатура для подтверждения вывода средств
def get_withdrawal_confirmation_keyboard(amount: float):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_withdrawal:{amount}"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_withdrawal")
    )
    return builder.as_markup()

# Клавиатура для реферальной программы
def get_referral_keyboard(ref_link: str):
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

# Для обратной совместимости
def get_payment_keyboard():
    """
    Создает клавиатуру с кнопкой оплаты для совместимости со старым кодом.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой оплаты
    """
    from config import DEPOSIT_AMOUNT_USD
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"💵 Пополнить баланс на ${DEPOSIT_AMOUNT_USD:.2f}",
        callback_data="deposit_balance"
    )
    builder.button(
        text="📊 История транзакций",
        callback_data="transaction_history"
    )
    return builder.as_markup()

# Клавиатура для подтверждения начала консультации
def get_consultation_confirmation_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Начать сейчас", callback_data="start_consultation"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="back_to_main_menu")
    )
    return builder.as_markup()