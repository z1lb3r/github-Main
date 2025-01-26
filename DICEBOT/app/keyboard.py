from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

#   ОСНОВНЫЕ КЛАВЫ REPLY
back_to_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Вернуться в главное меню")]],
                                    resize_keyboard=True)


search_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Начать поиск")],
                                          [KeyboardButton(text="Депозит")],
                                          [KeyboardButton(text="Вывести")]],
                                resize_keyboard=True)


cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отменить поиск")],
               [KeyboardButton(text="Вернуться в главное меню")],],
                                          resize_keyboard=True)


startgame_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Запустить игру")]],
                                resize_keyboard=True)


throwdice_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Кинуть кубик!")],
                                             [KeyboardButton(text="Покинуть игру")],],
                                resize_keyboard=True)