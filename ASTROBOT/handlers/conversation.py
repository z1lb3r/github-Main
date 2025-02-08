from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from services.db import user_has_active_subscription
from services.rag_utils import answer_with_rag

router = Router()

@router.message()
async def conversation_handler(message: Message, state: FSMContext):
    # Если пользователь находится в процессе прохождения анкеты – не обрабатываем сообщение
    current_state = await state.get_state()
    if current_state is not None:
        return

    if not user_has_active_subscription(message.from_user.id):
        await message.answer("Подписка неактивна. Введите /subscribe.")
        return

    data = await state.get_data()
    conversation_history = data.get("conversation_history", "")
    
    # Ограничиваем диалог 4 вопросами
    question_count = data.get("question_count", 0)
    if question_count >= 4:
        await message.answer("за#бал, больше общаться не буду, пшел вон!")
        await state.update_data(conversation_history="", question_count=0)
        return

    # Добавляем новое сообщение пользователя в историю
    conversation_history += f"Пользователь: {message.text}\n"
    
    # Формируем полный prompt, включающий всю историю диалога
    full_prompt = f"История диалога:\n{conversation_history}\n\nВопрос: {message.text}"
    
    # holos_response сохраняется из предыдущей сессии
    holos_response = data.get("holos_response", {})
    
    # Для последующих ответов используем режим "free" с ограничением ~200 слов (600 токенов)
    answer = answer_with_rag(full_prompt, holos_response, mode="free", conversation_history=conversation_history, max_tokens=600)
    
    # Добавляем ответ бота в историю
    conversation_history += f"Бот: {answer}\n"
    question_count += 1
    await state.update_data(conversation_history=conversation_history, question_count=question_count)
    
    await message.answer(answer)
