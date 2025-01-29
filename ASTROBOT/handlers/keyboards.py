from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Подписка"),
            KeyboardButton(text="Расчёт композита"),
            KeyboardButton(text="Расчёт Dream Rave")
        ]
    ],
    resize_keyboard=True
)