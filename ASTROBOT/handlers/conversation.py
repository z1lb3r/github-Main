"""
Обработчик обычных сообщений пользователя.
Обрабатывает все сообщения, которые не обработаны другими обработчиками.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from services.db import user_has_active_subscription
from services.rag_utils import answer_with_rag

router = Router()

@router.message()
async def conversation_handler(message: Message, state: FSMContext):
    """
    Обработчик обычных сообщений пользователя.
    Генерирует ответы с помощью RAG, отслеживает историю диалога.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    # Если пользователь находится в процессе прохождения анкеты – не обрабатываем сообщение
    current_state = await state.get_state()
    if current_state is not None:
        return

    # Проверяем наличие активной подписки
    if not user_has_active_subscription(message.from_user.id):
        await message.answer("Подписка неактивна. Введите /subscribe для активации.")
        return

    # Получаем данные из состояния
    data = await state.get_data()
    conversation_history = data.get("conversation_history", "")
    
    # Ограничиваем диалог 4 вопросами
    question_count = data.get("question_count", 0)
    if question_count >= 4:
        await message.answer("Достигнут лимит вопросов. Пожалуйста, начните новую сессию.")
        await state.update_data(conversation_history="", question_count=0)
        return

    # Добавляем новое сообщение пользователя в историю
    conversation_history += f"Пользователь: {message.text}\n"
    
    # Формируем полный prompt, включающий всю историю диалога
    full_prompt = f"История диалога:\n{conversation_history}\n\nВопрос: {message.text}"
    
    # Получаем данные Holos из предыдущей сессии
    holos_response = data.get("holos_response", {})
    
    # Генерируем ответ с помощью RAG
    answer = answer_with_rag(
        full_prompt, 
        holos_response, 
        mode="free", 
        conversation_history=conversation_history, 
        max_tokens=600
    )
    
    # Добавляем ответ бота в историю
    conversation_history += f"Бот: {answer}\n"
    question_count += 1
    
    # Сохраняем обновленную историю и счетчик вопросов
    await state.update_data(
        conversation_history=conversation_history, 
        question_count=question_count
    )
    
    # Отправляем ответ пользователю
    await message.answer(answer)