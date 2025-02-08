from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from services.db import get_user_profile, user_has_active_subscription
from services.holos_api import send_request_to_holos

router = Router()

@router.message(lambda msg: msg.text and msg.text.lower() == "хьюман дизайн")
async def handle_human_design(message: Message, state: FSMContext):
    if not user_has_active_subscription(message.from_user.id):
        await message.answer("У вас нет активной подписки. Введите /subscribe для активации.")
        return

    profile = get_user_profile(message.from_user.id)
    if not profile:
        await message.answer("Ваш профиль не заполнен. Для заполнения данных выберите 'Изменить данные' или введите /start.")
        return

    # Формируем строку даты и времени рождения
    date_str = f"{profile['birth_date']} {profile['birth_time']}"  # формат: ГГГГ-ММ-ДД ЧЧ:ММ
    latitude = profile["latitude"]
    longitude = profile["longitude"]
    altitude = profile["altitude"]

    from config import HOLOS_DREAM_URL
    response_data = await send_request_to_holos(
        holos_url=HOLOS_DREAM_URL,
        date_str=date_str,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude
    )
    
    # Собираем данные пользователя в виде строки (информация из базы + API)
    user_profile_info = (
        f"Дата рождения: {profile['birth_date']}\n"
        f"Время рождения: {profile['birth_time']}\n"
        f"Место рождения (координаты): {latitude}, {longitude}, {altitude}\n"
        f"Данные API: {response_data}"
    )
    
    holos_data_combined = {
        "user_profile": user_profile_info,
        "api_response": response_data
    }
    
    from services.rag_utils import answer_with_rag
    # Режим "4_aspects": первый ответ должен определить тип личности и дать рекомендации
    expert_comment = answer_with_rag(
        "Проанализируй данные и дай описание и практические рекомендации по 4 аспектам: отношения/любовь, финансы, здоровье, источники счастья.",
        holos_data_combined,
        mode="4_aspects",
        conversation_history="",
        max_tokens=1200
    )
    # Выводим первичный ответ
    if len(expert_comment) > 4096:
        chunk_size = 4096
        for i in range(0, len(expert_comment), chunk_size):
            await message.answer(expert_comment[i:i+chunk_size])
    else:
        await message.answer(expert_comment)
    await message.answer("Я собрал необходимые данные и дал комментарий. Теперь можешь задать до 4 вопросов по теме.")
    
    # Сохраняем начальную историю диалога и данные API в состоянии, чтобы последующие вопросы учитывали контекст
    await state.update_data(
        conversation_history=f"Бот: {expert_comment}\n",
        question_count=0,
        holos_response=holos_data_combined
    )
