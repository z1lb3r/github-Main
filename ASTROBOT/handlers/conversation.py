from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from services.db import user_has_active_subscription
from services.rag_utils import answer_with_rag

router = Router()

@router.message()
async def conversation_handler(message: Message, state: FSMContext):
    if not user_has_active_subscription(message.from_user.id):
        await message.answer("Подписка неактивна. Введите /subscribe.")
        return

    user_question = message.text
    # Из состояния можем получить holos_response, если это нужно для дальнейшего контекста.
    data = await state.get_data()
    holos_response = data.get("holos_response", {})

    # Вызываем функцию RAG, которая использует заранее подготовленный book1.index/chunks.npy
    expert_comment = answer_with_rag(user_question, holos_response)
    if len(expert_comment) > 4096:
        # Если слишком длинно, разбиваем на части
        from handlers.calculations import send_long_message
        await send_long_message(message, expert_comment)
    else:
        await message.answer(expert_comment)