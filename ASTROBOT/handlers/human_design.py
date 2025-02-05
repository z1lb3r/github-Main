from aiogram import Router
from aiogram.types import Message
from services.db import get_user_profile, user_has_active_subscription
from services.holos_api import send_request_to_holos

router = Router()

@router.message(lambda msg: msg.text and msg.text.lower() == "хьюман дизайн")
async def handle_human_design(message: Message):
    if not user_has_active_subscription(message.from_user.id):
        await message.answer("У вас нет активной подписки. Введите /subscribe для активации.")
        return

    profile = get_user_profile(message.from_user.id)
    if not profile:
        await message.answer("Ваш профиль не заполнен. Для заполнения данных выберите 'Изменить данные' или введите /start.")
        return

    # Объединяем дату и время в один запрос в нужном формате
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

    # Формируем новый запрос для ChatGPT:
    from services.rag_utils import answer_with_rag
    expert_comment = answer_with_rag(
        "Проанализируй данные и дай описание и практические рекомендации по 4 аспектам: отношения/любовь, финансы, здоровье, источники счастья.",
        response_data
    )
    if len(expert_comment) > 4096:
        chunk_size = 4096
        for i in range(0, len(expert_comment), chunk_size):
            await message.answer(expert_comment[i:i+chunk_size])
    else:
        await message.answer(expert_comment)
    await message.answer("Я собрал необходимые данные и дал комментарий. Задавайте интересующие вопросы.")
