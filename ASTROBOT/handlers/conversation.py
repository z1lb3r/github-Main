from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from services.db import user_has_active_subscription
from services.pdf_data import get_pdf_content
#from services.chat_gpt import get_esoteric_astrology_response
from services.chat_gpt import get_expert_comment
from handlers.calculations import send_long_message

router = Router()

@router.message()
async def conversation_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not user_has_active_subscription(user_id):
        await message.answer("Подписка неактивна. Введите /subscribe.")
        return

    user_question = message.text
    data = await state.get_data()
    holos_response = data.get("holos_response", {})

    pdf_content = get_pdf_content()
 #   answer = get_esoteric_astrology_response(user_question, pdf_content, holos_response)
 #   answer = get_esoteric_astrology_response(user_question, holos_response)
    comment = get_expert_comment(user_question, holos_response)
    if len(comment) > 4096:
        # Разбить и отправить
        await send_long_message(message, comment)
    else:
        await message.answer(comment)

    