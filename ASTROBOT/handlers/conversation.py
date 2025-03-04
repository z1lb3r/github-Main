"""
Обработчик обычных сообщений пользователя.
Обрабатывает все сообщения, которые не обработаны другими обработчиками.
Реализует систему списания средств за использование бота.
"""

import math
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.db import get_user_balance, subtract_from_balance
from services.rag_utils import answer_with_rag, count_tokens
from config import (
    TOKEN_PRICE, 
    MIN_REQUIRED_BALANCE, 
    DEPOSIT_AMOUNT_USD, 
    DISPLAY_CURRENCY,
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
    и списывает средства за использование только в режиме консультации.
    
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
    
    # Добавляем новое сообщение пользователя в историю независимо от режима
    conversation_history = data.get("conversation_history", "")
    conversation_history += f"Пользователь: {message.text}\n"
    
    # Обновляем историю диалога в состоянии
    await state.update_data(conversation_history=conversation_history)
    
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
            text=f"Пополнить баланс (${DEPOSIT_AMOUNT_USD:.2f})",
            callback_data="deposit_balance"
        )
        await message.answer(
            f"⚠️ Недостаточно средств на балансе!\n\n"
            f"Ваш текущий баланс: ${balance:.2f}\n"
            f"Минимальный баланс для консультации: ${MIN_REQUIRED_BALANCE:.2f}\n\n"
            "Пожалуйста, пополните баланс для продолжения консультации.",
            reply_markup=builder.as_markup()
        )
        return

    # Формируем полный prompt, включающий всю историю диалога
    full_prompt = f"История диалога:\n{conversation_history}\n\nВопрос: {message.text}"
    
    # Получаем данные Holos из предыдущей сессии
    holos_response = data.get("holos_response", {})
    
    # Подсчитываем количество токенов во входящем сообщении
    input_tokens = count_tokens(message.text)
    
    # Оцениваем стоимость запроса (используем множитель для входящих токенов)
    estimated_cost = input_tokens * TOKEN_PRICE * INPUT_TOKEN_MULTIPLIER
    
    # Проверяем, хватает ли средств на обработку запроса
    if balance < estimated_cost:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=f"Пополнить баланс (${DEPOSIT_AMOUNT_USD:.2f})",
            callback_data="deposit_balance"
        )
        await message.answer(
            f"⚠️ Недостаточно средств для обработки этого сообщения!\n\n"
            f"Требуется: ${estimated_cost:.6f}\n"
            f"Ваш баланс: ${balance:.6f}\n\n"
            f"Стоимость обработки: {input_tokens} токенов × ${TOKEN_PRICE:.6f} × {INPUT_TOKEN_MULTIPLIER} = ${estimated_cost:.6f}\n\n"
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
    
    # Уведомляем пользователя о списании средств
    await message.answer(
        f"💸 С вашего баланса списано ${estimated_cost:.6f} за обработку запроса.\n"
        f"Обрабатываем ваш запрос..."
    )
    
    # Генерируем ответ с помощью RAG
    answer = answer_with_rag(
        full_prompt, 
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
            text=f"Пополнить баланс (${DEPOSIT_AMOUNT_USD:.2f})",
            callback_data="deposit_balance"
        )
        await message.answer(
            f"⚠️ Недостаточно средств для получения полного ответа!\n\n"
            f"Требуется: ${response_cost:.6f}\n"
            f"Ваш баланс: ${remaining_balance:.6f}\n\n"
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
    
    # Добавляем ответ бота в историю
    conversation_history += f"Бот: {answer}\n"
    
    # Сохраняем обновленную историю
    await state.update_data(conversation_history=conversation_history)
    
    # Отправляем ответ пользователю с информацией о стоимости
    new_balance = get_user_balance(user_id)
    
    await message.answer(
        f"{answer}\n\n"
        f"💸 Стоимость ответа: ${response_cost:.6f} ({output_tokens} токенов)\n"
        f"💰 Ваш текущий баланс: ${new_balance:.6f}",
        reply_markup=get_end_consultation_keyboard()
    )   