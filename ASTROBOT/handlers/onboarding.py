"""
Обработчики для онбординга новых пользователей.
Реализует анкетирование для сбора данных о пользователе.
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import aiohttp
import asyncio
import json

from services.db import update_user_profile
from .keyboards import main_menu_kb

# Создаем экземпляр роутера
router = Router()

# Определяем состояния для FSM
class OnboardingStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_birth_date = State()
    waiting_for_birth_time = State()
    waiting_for_birth_location = State()

# Функция геокодирования для получения координат по названию места
async def geocode_location(location_text: str):
    """
    Получает географические координаты и высоту по названию места с помощью Nominatim API.
    
    Args:
        location_text (str): Название места для геокодирования (например, "Москва, Россия")
        
    Returns:
        tuple: (latitude, longitude, altitude) или (0.0, 0.0, 0.0) в случае ошибки
    """
    print(f"Геокодирование местоположения: {location_text}")
    
    # Нейтральные значения по умолчанию
    default_latitude = 0.0
    default_longitude = 0.0
    default_altitude = 0.0
    
    try:
        # Делаем запрос к Nominatim API (OpenStreetMap)
        nominatim_url = "https://nominatim.openstreetmap.org/search"
        
        params = {
            "q": location_text,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        
        headers = {
            "User-Agent": "AstroBot/1.0"  # Nominatim требует User-Agent
        }
        
        # Выполняем запрос
        async with aiohttp.ClientSession() as session:
            async with session.get(nominatim_url, params=params, headers=headers) as response:
                if response.status != 200:
                    print(f"Ошибка API Nominatim: HTTP {response.status}")
                    return default_latitude, default_longitude, default_altitude
                
                data = await response.json()
                
                if not data:
                    print(f"Место '{location_text}' не найдено")
                    return default_latitude, default_longitude, default_altitude
                
                # Получаем координаты
                latitude = float(data[0]["lat"])
                longitude = float(data[0]["lon"])
                
                # Делаем задержку перед вторым запросом (согласно политике использования API)
                await asyncio.sleep(1)
                
                # Теперь запрашиваем высоту через Open-Elevation API
                try:
                    elevation_url = "https://api.open-elevation.com/api/v1/lookup"
                    elevation_params = {
                        "locations": f"{latitude},{longitude}"
                    }
                    
                    async with session.get(elevation_url, params=elevation_params) as elev_response:
                        if elev_response.status == 200:
                            elev_data = await elev_response.json()
                            altitude = elev_data["results"][0]["elevation"]
                            print(f"Получены координаты: {latitude}, {longitude}, высота: {altitude}")
                        else:
                            altitude = default_altitude
                            print(f"Не удалось получить данные о высоте, используем значение по умолчанию")
                except Exception as e:
                    altitude = default_altitude
                    print(f"Ошибка при получении высоты: {str(e)}")
                
                return latitude, longitude, altitude
                
    except Exception as e:
        print(f"Ошибка геокодирования: {str(e)}")
        return default_latitude, default_longitude, default_altitude

# Функция для начала онбординга
async def start_onboarding(message: Message, state: FSMContext):
    """
    Начинает процесс онбординга (анкетирования) пользователя.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния FSM
    """
    await state.set_state(OnboardingStates.waiting_for_name)
    await message.answer("Пожалуйста, введите ваше полное имя:")

# Обработчик ввода имени
@router.message(OnboardingStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """
    Обрабатывает ввод имени пользователя.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния FSM
    """
    # Сохраняем имя в данных состояния
    await state.update_data(full_name=message.text)
    
    # Переходим к следующему состоянию
    await state.set_state(OnboardingStates.waiting_for_birth_date)
    
    # Запрашиваем дату рождения
    await message.answer(
        "Спасибо! Теперь введите дату вашего рождения в формате ГГГГ-ММ-ДД.\n"
        "Например: 1990-01-15"
    )

# Обработчик ввода даты рождения
@router.message(OnboardingStates.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    """
    Обрабатывает ввод даты рождения пользователя.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния FSM
    """
    # Проверяем формат даты
    date_text = message.text.strip()
    
    # Очень простая проверка формата даты
    date_parts = date_text.split('-')
    if len(date_parts) != 3 or len(date_text) < 8:
        await message.answer(
            "Пожалуйста, введите дату в формате ГГГГ-ММ-ДД.\n"
            "Например: 1990-01-15"
        )
        return
    
    # Сохраняем дату рождения в данных состояния
    await state.update_data(birth_date=date_text)
    
    # Переходим к следующему состоянию
    await state.set_state(OnboardingStates.waiting_for_birth_time)
    
    # Запрашиваем время рождения
    await message.answer(
        "Спасибо! Теперь введите время вашего рождения в формате ЧЧ:ММ.\n"
        "Например: 14:30"
    )

# Обработчик ввода времени рождения
@router.message(OnboardingStates.waiting_for_birth_time)
async def process_birth_time(message: Message, state: FSMContext):
    """
    Обрабатывает ввод времени рождения пользователя.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния FSM
    """
    # Проверяем формат времени
    time_text = message.text.strip()
    
    # Очень простая проверка формата времени
    if len(time_text.split(':')) != 2 or len(time_text) < 4:
        await message.answer(
            "Пожалуйста, введите время в формате ЧЧ:ММ.\n"
            "Например: 14:30"
        )
        return
    
    # Сохраняем время рождения в данных состояния
    await state.update_data(birth_time=time_text)
    
    # Переходим к следующему состоянию
    await state.set_state(OnboardingStates.waiting_for_birth_location)
    
    # Запрашиваем место рождения
    await message.answer(
        "Почти готово! Теперь введите место вашего рождения (город, страна).\n"
        "Например: Москва, Россия или London, UK"
    )

# Обработчик ввода места рождения
@router.message(OnboardingStates.waiting_for_birth_location)
async def process_birth_location(message: Message, state: FSMContext):
    """
    Обрабатывает ввод места рождения пользователя.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния FSM
    """
    # Получаем место рождения и геокодируем его
    location_text = message.text.strip()
    
    # Сообщаем пользователю, что идет обработка
    await message.answer("Определяю координаты места рождения...")
    
    try:
        # Геокодируем местоположение
        latitude, longitude, altitude = await geocode_location(location_text)
        
        # Сохраняем координаты в данных состояния
        await state.update_data(
            birth_location=location_text,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude
        )
        
        # Получаем все данные из состояния
        data = await state.get_data()
        
        # Обновляем профиль пользователя в базе данных
        update_user_profile(
            message.from_user.id,
            data.get('full_name'),
            data.get('birth_date'),
            data.get('birth_time'),
            latitude,
            longitude,
            altitude
        )
        
        # Проверяем, пришел ли пользователь по приглашению для проверки совместимости
        if 'start_invite_code' in data:
            invite_code = data['start_invite_code']
            from handlers.compatibility import process_compatibility_invitation
            await process_compatibility_invitation(message, invite_code)
        
        # Завершаем состояние
        await state.clear()
        
        # Отправляем финальное сообщение
        await message.answer(
            "🎉 Отлично! Ваши данные сохранены.\n\n"
            f"Имя: {data.get('full_name')}\n"
            f"Дата рождения: {data.get('birth_date')}\n"
            f"Время рождения: {data.get('birth_time')}\n"
            f"Место рождения: {location_text}\n"
            f"Координаты: {latitude}, {longitude}\n"
            f"Высота над уровнем моря: {altitude} м\n\n"
            "Теперь вы можете использовать все функции бота!",
            reply_markup=main_menu_kb
        )
    except Exception as e:
        print(f"Ошибка при обработке местоположения: {str(e)}")
        await message.answer(
            "Произошла ошибка при определении координат. "
            "Пожалуйста, попробуйте ввести более точное название города или другой город."
        )