from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Text

from config import HOLOS_COMPOSITE_URL, HOLOS_DREAM_URL
from services.db import user_has_active_subscription
from services.holos_api import send_request_to_holos
from services.pdf_data import get_pdf_content
from services.chat_gpt import get_section_comment

router = Router()

class CalculationStates(StatesGroup):
    waiting_for_choice = State()
    waiting_for_date = State()
    waiting_for_latitude = State()
    waiting_for_longitude = State()
    waiting_for_altitude = State()

@router.message(Text(equals=["Расчёт композита", "Расчёт Dream Rave"], ignore_case=True))
async def start_calculation(message: Message, state: FSMContext):
    """Пользователь выбрал один из расчётов: композит или Dream Rave."""
    user_id = message.from_user.id
    if not user_has_active_subscription(user_id):
        await message.answer("У вас нет активной подписки. Используйте /subscribe.")
        return

    chosen_section = message.text.strip().lower()  # «расчёт композита» или «расчёт dream rave»
    await state.update_data(chosen_section=chosen_section)

    # Спрашиваем дату
    await message.answer("Укажите дату (ГГГГ-ММ-ДД):")
    await state.set_state(CalculationStates.waiting_for_date)

@router.message(CalculationStates.waiting_for_date)
async def handle_date(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not user_has_active_subscription(user_id):
        await message.answer("Подписка неактивна. Введите /subscribe.")
        return

    date_str = message.text.strip()
    # Здесь можно валидировать формат ГГГГ-ММ-ДД
    await state.update_data(date=date_str)

    await message.answer("Укажите широту (например, 55.7558):")
    await state.set_state(CalculationStates.waiting_for_latitude)

@router.message(CalculationStates.waiting_for_latitude)
async def handle_latitude(message: Message, state: FSMContext):
    lat_str = message.text.strip()
    try:
        lat = float(lat_str)
    except ValueError:
        await message.answer("Широта должна быть числом. Попробуйте снова.")
        return

    await state.update_data(latitude=lat)
    await message.answer("Укажите долготу (например, 37.6173):")
    await state.set_state(CalculationStates.waiting_for_longitude)

@router.message(CalculationStates.waiting_for_longitude)
async def handle_longitude(message: Message, state: FSMContext):
    lon_str = message.text.strip()
    try:
        lon = float(lon_str)
    except ValueError:
        await message.answer("Долгота должна быть числом. Попробуйте снова.")
        return

    await state.update_data(longitude=lon)
    await message.answer("Укажите высоту над уровнем моря (например, 200):")
    await state.set_state(CalculationStates.waiting_for_altitude)

@router.message(CalculationStates.waiting_for_altitude)
async def handle_altitude(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not user_has_active_subscription(user_id):
        await message.answer("Подписка неактивна. Введите /subscribe.")
        return

    alt_str = message.text.strip()
    try:
        alt = float(alt_str)
    except ValueError:
        await message.answer("Высота должна быть числом. Попробуйте снова.")
        return

    data = await state.get_data()
    chosen_section = data["chosen_section"]  # «расчёт композита» или «расчёт dream rave»

    data["altitude"] = alt
    # Выбираем URL в зависимости от раздела
    if "композита" in chosen_section:
        holos_url = HOLOS_COMPOSITE_URL
    else:
        holos_url = HOLOS_DREAM_URL

    # Формируем запрос
    date_value = data["date"]
    lat_value = data["latitude"]
    lon_value = data["longitude"]
    alt_value = data["altitude"]

    # Отправляем запрос
    response_data = await send_request_to_holos(
        holos_url=holos_url,
        date_str=date_value,
        latitude=lat_value,
        longitude=lon_value,
        altitude=alt_value
    )

    # Сохраняем ответ
    await state.update_data(holos_response=response_data)
    await state.clear()

    # Дополнительный комментарий в зависимости от раздела:
    pdf_content = get_pdf_content()
    comment_text = get_section_comment(section_name=chosen_section, pdf_content=pdf_content, holos_data=response_data)

    await message.answer(
        "Я собрал необходимые данные для продолжения диалога. Задавай интересующий вопрос.\n\n"
        f"{comment_text}"
    )