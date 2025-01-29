from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from services.db import user_has_active_subscription
from services.pdf_data import get_pdf_content
from services.chat_gpt import get_esoteric_astrology_response

router = Router()

@router.message()
async def conversation_handler(message: Message, state: FSMContext):
    """Свободный диалог после получения данных."""
    user_id = message.from_user.id
    if not user_has_active_subscription(user_id):
        await message.answer("Подписка неактивна. Введите /subscribe.")
        return

    user_question = message.text

    data = await state.get_data()
    holos_response = data.get("holos_response", {})

    pdf_content = get_pdf_content()

    # Получаем ответ от ChatGPT
    answer = get_esoteric_astrology_response(
        user_input=user_question,
        pdf_content=pdf_content,
        holos_data=holos_response
    )

    await message.answer(answer)