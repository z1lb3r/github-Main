from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from services.db import user_has_active_subscription
from services.rag_utils import answer_with_rag

router = Router()

@router.message()
async def conversation_handler(message: Message, state: FSMContext):
    # Если пользователь находится в процессе прохождения анкеты или изменения данных – не обрабатываем сообщение
    current_state = await state.get_state()
    if current_state is not None:
        return

    if not user_has_active_subscription(message.from_user.id):
        await message.answer("Подписка неактивна. Введите /subscribe.")
        return

    user_question = message.text
    data = await state.get_data()
    holos_response = data.get("holos_response", {})

    # Используем свободный режим (mode по умолчанию "free")
    expert_comment = answer_with_rag(user_question, holos_response)
    if len(expert_comment) > 4096:
        from handlers.human_design import send_long_message
        await send_long_message(message, expert_comment)
    else:
        await message.answer(expert_comment)
