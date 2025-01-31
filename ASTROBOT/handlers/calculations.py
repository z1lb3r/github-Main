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
    """Функция для отправки очень длинных сообщений по частям."""
    chunk_size = 4096
    if len(text) <= chunk_size:
        await message.answer(text)
    else:
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            await message.answer(chunk)


@router.message(lambda msg: msg.text and msg.text.lower() in ["расчёт композита", "расчёт dream rave"])
async def start_calculation(message: Message, state: FSMContext):
    """Начинаем опрос, чтобы собрать данные для запроса к Holos."""
    user_id = message.from_user.id
    if not user_has_active_subscription(user_id):
        await message.answer("У вас нет активной подписки. Введите /subscribe для активации.")
        return

    chosen_section = message.text.strip().lower()  # «расчёт композита» или «расчёт dream rave»
    await state.update_data(chosen_section=chosen_section)

    await message.answer("Укажите дату (ГГГГ-ММ-ДД):")
    await state.set_state(CalculationStates.waiting_for_date)

@router.message(CalculationStates.waiting_for_date)
async def handle_date(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not user_has_active_subscription(user_id):
        await message.answer("Подписка неактивна. /subscribe")
        return

    date_str = message.text.strip()
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
        await message.answer("Долгота должна быть числом. Повторите снова.")
        return

    await state.update_data(longitude=lon)
    await message.answer("Укажите высоту над уровнем моря (например, 200):")
    await state.set_state(CalculationStates.waiting_for_altitude)

@router.message(CalculationStates.waiting_for_altitude)
async def handle_altitude(message: Message, state: FSMContext):
    """Завершаем опрос, отправляем запрос к Holos, показываем пользователю сырые результаты JSON."""
    user_id = message.from_user.id
    if not user_has_active_subscription(user_id):
        await message.answer("Подписка неактивна. Введите /subscribe.")
        return

    alt_str = message.text.strip()
    try:
        alt = float(alt_str)
    except ValueError:
        await message.answer("Высота должна быть числом. Повторите снова.")
        return

    data = await state.get_data()
    data["altitude"] = alt

    chosen_section = data["chosen_section"]  # «расчёт композита» или «расчёт dream rave»
    if "композита" in chosen_section:
        holos_url = HOLOS_COMPOSITE_URL
    else:
        holos_url = HOLOS_DREAM_URL

    date_value = data["date"]
    lat_value = data["latitude"]
    lon_value = data["longitude"]
    alt_value = data["altitude"]

    # Отправляем запрос к Holos
    response_data = await send_request_to_holos(
        holos_url=holos_url,
        date_str=date_value,
        latitude=lat_value,
        longitude=lon_value,
        altitude=alt_value
    )

    # Сохраняем результат в состояние, чтобы дальше его мог использовать ChatGPT
    await state.update_data(holos_response=response_data)

    # Очищаем FSM (опрос закончен)
    await state.clear()

    # ----- ВАЖНО: Теперь вместо комментария от ChatGPT сразу показываем сырые результаты -----

    # Показываем пользователю результат
    # await message.answer(
    #     "Вот результаты запроса к Holos:\n\n"
    #     f"{response_data}"  # Можно форматировать, если нужно
    # )
    #   ОТМЕНЯЕМ ВЫВОД СЫРЫХ ДАННЫХ С АПИ
    # text_to_send = "Вот результаты запроса к Holos:\n\n" + str(response_data)
    # await send_long_message(message, text_to_send)

    from services.chat_gpt import get_expert_comment
    comment = get_expert_comment(
        user_input="Проанализируй эти данные и дай рекомендации по Human Design",
        holos_data=response_data
    )

    # 4) Отправляем ответ
    if len(comment) > 4096:
        await send_long_message(message, comment)
    else:
        await message.answer(comment)

    # 5) Пишем фразу, что бот готов к дополнительным вопросам
    await message.answer("Я собрал необходимые данные и дал комментарий. Задавайте интересующие вопросы.")