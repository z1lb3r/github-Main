"""
Клавиатуры для Telegram-бота.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Клавиатура главного меню
main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Подписка"),
            KeyboardButton(text="Хьюман дизайн")
        ],
        [
            KeyboardButton(text="Гороскоп"),
            KeyboardButton(text="Изменить данные")
        ]
    ],
    resize_keyboard=True
)