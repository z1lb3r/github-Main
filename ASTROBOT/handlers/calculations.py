from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import HOLOS_COMPOSITE_URL, HOLOS_DREAM_URL
from services.db import user_has_active_subscription
from services.holos_api import send_request_to_holos

router = Router()

class CalculationStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_latitude = State()
    waiting_for_longitude = State()
    waiting_for_altitude = State()

async def send_long_message(message, text: str):
    chunk_size = 4096
    if len(text) <= chunk_size:
        await message.answer(text)
    else:
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            await message.answer(chunk)

@router.message(lambda msg: msg.text and msg.text.lower() in ["расчёт композита", "расчёт dream rave"])
async def start_calculation(message: Message, state: FSMContext):
    if not user_has_active_subscription(message.from_user.id):
        await message.answer("У вас нет активной подписки. Введите /subscribe для активации.")
        return

    chosen_section = message.text.strip().lower()  # либо "расчёт композита" либо "расчёт dream rave"
    await state.update_data(chosen_section=chosen_section)
    await message.answer("Укажите дату (ГГГГ-ММ-ДД):")
    await state.set_state(CalculationStates.waiting_for_date)

@router.message(CalculationStates.waiting_for_date)
async def handle_date(message: Message, state: FSMContext):
    if not user_has_active_subscription(message.from_user.id):
        await message.answer("Подписка неактивна. /subscribe")
        return

    await state.update_data(date=message.text.strip())
    await message.answer("Укажите широту (например, 55.7558):")
    await state.set_state(CalculationStates.waiting_for_latitude)

@router.message(CalculationStates.waiting_for_latitude)
async def handle_latitude(message: Message, state: FSMContext):
    try:
        lat = float(message.text.strip())
    except ValueError:
        await message.answer("Широта должна быть числом. Попробуйте снова.")
        return
    await state.update_data(latitude=lat)
    await message.answer("Укажите долготу (например, 37.6173):")
    await state.set_state(CalculationStates.waiting_for_longitude)

@router.message(CalculationStates.waiting_for_longitude)
async def handle_longitude(message: Message, state: FSMContext):
    try:
        lon = float(message.text.strip())
    except ValueError:
        await message.answer("Долгота должна быть числом. Повторите снова.")
        return
    await state.update_data(longitude=lon)
    await message.answer("Укажите высоту над уровнем моря (например, 200):")
    await state.set_state(CalculationStates.waiting_for_altitude)

@router.message(CalculationStates.waiting_for_altitude)
async def handle_altitude(message: Message, state: FSMContext):
    try:
        alt = float(message.text.strip())
    except ValueError:
        await message.answer("Высота должна быть числом. Повторите снова.")
        return

    data = await state.get_data()
    data["altitude"] = alt
    chosen_section = data["chosen_section"]
    holos_url = HOLOS_COMPOSITE_URL if "композита" in chosen_section else HOLOS_DREAM_URL

    response_data = await send_request_to_holos(
        holos_url=holos_url,
        date_str=data["date"],
        latitude=data["latitude"],
        longitude=data["longitude"],
        altitude=data["altitude"]
    )
    await state.update_data(holos_response=response_data)
    await state.clear()

    # После запроса не выводим сырые данные, а переходим к получению экспертного комментария.
    from services.rag_utils import answer_with_rag  # Функция, которая использует book1.pdf через embeddings
    expert_comment = answer_with_rag("Проанализируй данные и дай рекомендации по Human Design", response_data)

    if len(expert_comment) > 4096:
        await send_long_message(message, expert_comment)
    else:
        await message.answer(expert_comment)

    await message.answer("Я собрал необходимые данные и дал комментарий. Задавайте интересующие вопросы.")