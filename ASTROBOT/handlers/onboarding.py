"""
Обработчики для процесса онбординга (заполнения анкеты) пользователя.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import aiohttp

from services.db import update_user_profile

router = Router()

class OnboardingStates(StatesGroup):
    """
    Состояния для FSM (Finite State Machine) процесса онбординга.
    """
    waiting_for_full_name = State()
    waiting_for_birth_date = State()
    waiting_for_birth_time = State()
    waiting_for_birth_city = State()

async def start_onboarding(message: Message, state: FSMContext):
    """
    Функция запуска процесса онбординга.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    await message.answer("Добро пожаловать! Для работы бота, пожалуйста, заполните анкету.\nВведите, пожалуйста, ваше имя и фамилию:")
    await state.set_state(OnboardingStates.waiting_for_full_name)

@router.message(OnboardingStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    """
    Обработчик ввода имени и фамилии пользователя.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    await state.update_data(full_name=message.text.strip())
    await message.answer("Введите дату рождения в формате ГГГГ-ММ-ДД:")
    await state.set_state(OnboardingStates.waiting_for_birth_date)

@router.message(OnboardingStates.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    """
    Обработчик ввода даты рождения пользователя.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    await state.update_data(birth_date=message.text.strip())
    await message.answer("Введите время рождения в формате ЧЧ:ММ:")
    await state.set_state(OnboardingStates.waiting_for_birth_time)

@router.message(OnboardingStates.waiting_for_birth_time)
async def process_birth_time(message: Message, state: FSMContext):
    """
    Обработчик ввода времени рождения пользователя.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    await state.update_data(birth_time=message.text.strip())
    await message.answer("Введите название города рождения:")
    await state.set_state(OnboardingStates.waiting_for_birth_city)

@router.message(OnboardingStates.waiting_for_birth_city)
async def process_birth_city(message: Message, state: FSMContext):
    """
    Обработчик ввода города рождения пользователя.
    Определяет координаты города и высоту над уровнем моря.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    city = message.text.strip()
    
    # Получаем координаты города
    coordinates = await get_coordinates(city)
    if not coordinates:
        await message.answer("Не удалось определить координаты для данного города. Попробуйте ввести другое название:")
        return
    
    lat, lon, alt = coordinates
    
    # Сохраняем координаты в состоянии
    await state.update_data(birth_latitude=lat, birth_longitude=lon, birth_altitude=alt)
    
    # Получаем все данные из состояния
    data = await state.get_data()
    user_id = message.from_user.id
    
    # Обновляем профиль пользователя в БД
    update_user_profile(
        user_id=user_id,
        full_name=data["full_name"],
        birth_date=data["birth_date"],
        birth_time=data["birth_time"],
        latitude=lat,
        longitude=lon,
        altitude=alt
    )
    
    # Очищаем состояние
    await state.clear()
    
    # Показываем главное меню
    from handlers.keyboards import main_menu_kb
    await message.answer(
        f"Анкета заполнена, {data['full_name']}!\nДобро пожаловать в главное меню.",
        reply_markup=main_menu_kb
    )

async def get_coordinates(city: str) -> tuple:
    """
    Получает координаты и высоту над уровнем моря для указанного города.
    
    Args:
        city (str): Название города
        
    Returns:
        tuple: Кортеж (широта, долгота, высота) или None, если координаты не найдены
    """
    # Устанавливаем User-Agent для запросов к API
    headers = {"User-Agent": "ASTROBOT/1.0 (contact@example.com)"}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Получаем координаты через OpenStreetMap
        params = {"q": city, "format": "json", "limit": 1}
        async with session.get("https://nominatim.openstreetmap.org/search", params=params) as resp:
            data = await resp.json()
            if not data:
                return None
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
        
        # Получаем высоту над уровнем моря через Open Elevation API
        params = {"locations": f"{lat},{lon}"}
        async with session.get("https://api.open-elevation.com/api/v1/lookup", params=params) as resp:
            if resp.status != 200:
                alt = 0
            else:
                try:
                    elev_data = await resp.json()
                    if "results" in elev_data and elev_data["results"]:
                        alt = elev_data["results"][0].get("elevation", 0)
                    else:
                        alt = 0
                except Exception:
                    alt = 0
    
    return lat, lon, alt