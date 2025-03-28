"""
Обработчик обычных сообщений пользователя.
Обрабатывает все сообщения, которые не обработаны другими обработчиками.
Реализует систему списания средств за использование бота и хранение истории сообщений.
"""

import math
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.db import (
    get_user_balance, 
    subtract_from_balance, 
    save_message, 
    get_last_messages, 
    get_message_count, 
    delete_old_messages
)
from services.rag_utils import answer_with_rag, count_tokens, summarize_messages
from config import (
    TOKEN_PRICE, 
    MIN_REQUIRED_BALANCE, 
    INPUT_TOKEN_MULTIPLIER,
    OUTPUT_TOKEN_MULTIPLIER
)
from handlers.consultation_mode import get_end_consultation_keyboard

router = Router()

@router.message()
async def conversation_handler(message: Message, state: FSMContext):
    """
    Обработчик обычных сообщений пользователя.
    Генерирует ответы с помощью RAG, отслеживает историю диалога,
    списывает средства за использование, и сохраняет историю сообщений с суммаризацией.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    # Если пользователь находится в процессе прохождения анкеты – не обрабатываем сообщение
    current_state = await state.get_state()
    if current_state is not None:
        return

    # Получаем данные из состояния
    data = await state.get_data()
    
    # Проверяем, находится ли пользователь в режиме консультации
    in_consultation = data.get("in_consultation", False)
    
    # Если не в режиме консультации, просто отвечаем без списания средств
    if not in_consultation:
        await message.answer(
            "Вы не находитесь в режиме консультации. Ваш баланс не будет списан, "
            "но я могу предоставить только ограниченные ответы. Чтобы начать полную консультацию "
            "с детальным анализом, пожалуйста, используйте кнопку 'Начать консультацию' в главном меню."
        )
        return

    # Проверяем наличие достаточного баланса
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    
    if balance < MIN_REQUIRED_BALANCE:
        # Если баланс недостаточен, предлагаем пополнить
        builder = InlineKeyboardBuilder()
        builder.button(
            text=f"Пополнить баланс",
            callback_data="deposit_balance"
        )
        await message.answer(
            f"⚠️ Недостаточно средств на балансе!\n\n"
            f"Ваш текущий баланс: {balance:.0f} баллов\n"
            f"Минимальный баланс для консультации: {MIN_REQUIRED_BALANCE:.0f} баллов\n\n"
            "Пожалуйста, пополните баланс для продолжения консультации.",
            reply_markup=builder.as_markup()
        )
        return
    
    # Сохраняем сообщение пользователя в базу данных
    save_message(user_id, 'user', message.text)

    # Подсчитываем количество токенов во входящем сообщении
    input_tokens = count_tokens(message.text)
    
    # Оцениваем стоимость запроса (используем множитель для входящих токенов)
    estimated_cost = input_tokens * TOKEN_PRICE * INPUT_TOKEN_MULTIPLIER
    
    # Проверяем, хватает ли средств на обработку запроса
    if balance < estimated_cost:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=f"Пополнить баланс",
            callback_data="deposit_balance"
        )
        await message.answer(
            f"⚠️ Недостаточно средств для обработки этого сообщения!\n\n"
            f"Требуется: {estimated_cost:.2f} баллов\n"
            f"Ваш баланс: {balance:.2f} баллов\n\n"
            "Пожалуйста, пополните баланс или отправьте более короткое сообщение.",
            reply_markup=builder.as_markup()
        )
        return
    
    # Списываем средства за обработку запроса
    success = subtract_from_balance(
        user_id, 
        estimated_cost, 
        f"Обработка запроса ({input_tokens} токенов)"
    )
    
    if not success:
        await message.answer(
            "Произошла ошибка при списании средств. Пожалуйста, попробуйте позже."
        )
        return
    
    # Получаем общее количество сообщений
    msg_count = get_message_count(user_id)
    print(f"[DEBUG] Общее количество сообщений пользователя {user_id}: {msg_count}")
    
    # Получаем историю диалога из базы данных
    messages_history = get_last_messages(user_id, 100)  # Запрашиваем до 100 сообщений
    print(f"[DEBUG] Получено {len(messages_history)} сообщений из БД")
    
    # Подсчитываем количество полных сообщений и суммаризаций
    full_messages = [msg for msg in messages_history if not msg['is_summary']]
    summary_messages = [msg for msg in messages_history if msg['is_summary']]
    print(f"[DEBUG] Полных сообщений: {len(full_messages)}, суммаризаций: {len(summary_messages)}")
    
    # Выводим идентификаторы суммаризаций для отладки
    if summary_messages:
        print(f"[DEBUG] Суммаризации:")
        for i, msg in enumerate(summary_messages[:3]):  # Выводим до 3 суммаризаций
            print(f"[DEBUG]   {i+1}. ID: {msg['id']}, timestamp: {msg['timestamp']}")
            print(f"[DEBUG]      Содержимое (первые 100 символов): {msg['content'][:100]}...")
    
    # Формируем строку истории для промпта
    conversation_history = ""
    for msg in messages_history:
        if msg['is_summary']:
            conversation_history += f"Краткое содержание предыдущего диалога: {msg['content']}\n\n"
        else:
            prefix = "Пользователь: " if msg['sender'] == 'user' else "Бот: "
            conversation_history += f"{prefix}{msg['content']}\n"
    
    # Получаем данные Holos из предыдущей сессии
    holos_response = data.get("holos_response", {})
    
    # Генерируем ответ с помощью RAG
    answer = answer_with_rag(
        message.text,  # Текущий вопрос пользователя
        holos_response, 
        mode="free", 
        conversation_history=conversation_history, 
        max_tokens=600
    )
    
    # Подсчитываем количество токенов в ответе
    output_tokens = count_tokens(answer)
    
    # Оцениваем стоимость ответа (используем множитель для исходящих токенов)
    response_cost = output_tokens * TOKEN_PRICE * OUTPUT_TOKEN_MULTIPLIER
    
    # Проверяем, хватает ли средств на получение ответа
    remaining_balance = get_user_balance(user_id)
    if remaining_balance < response_cost:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=f"Пополнить баланс",
            callback_data="deposit_balance"
        )
        await message.answer(
            f"⚠️ Недостаточно средств для получения полного ответа!\n\n"
            f"Требуется: {response_cost:.2f} баллов\n"
            f"Ваш баланс: {remaining_balance:.2f} баллов\n\n"
            "Пожалуйста, пополните баланс для получения полного ответа.",
            reply_markup=builder.as_markup()
        )
        return
    
    # Списываем средства за получение ответа
    success = subtract_from_balance(
        user_id, 
        response_cost, 
        f"Получение ответа ({output_tokens} токенов)"
    )
    
    if not success:
        await message.answer(
            "Произошла ошибка при списании средств за ответ. Пожалуйста, попробуйте позже."
        )
        return
    
    # Сохраняем ответ бота в базу данных
    save_message(user_id, 'bot', answer)
    
    # Если сообщений больше 100, обрабатываем старые
    if msg_count > 100:
        # Получаем самые старые сообщения (те, которые нужно суммаризировать)
        old_messages = get_last_messages(user_id, 100)[:-20]  # Исключаем 20 последних
        print(f"[DEBUG] Суммаризируем {len(old_messages)} старых сообщений")
        
        # Суммаризируем старые сообщения
        summary = summarize_messages(old_messages)
        
        # Сохраняем суммаризацию как новое сообщение
        save_message(user_id, 'summary', summary, True)
        print(f"[DEBUG] Создана и сохранена суммаризация: {summary[:100]}...")
        
        # Удаляем старые сообщения
        deleted_count = delete_old_messages(user_id, 21)  # Оставляем 20 последних + 1 суммаризацию
        print(f"[DEBUG] Удалено {deleted_count} старых сообщений")
    
    # Отправляем ответ пользователю без информации о стоимости
    await message.answer(
        answer,
        reply_markup=get_end_consultation_keyboard()
    )