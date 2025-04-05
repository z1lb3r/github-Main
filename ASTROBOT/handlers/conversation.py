"""
Обработчик обычных сообщений пользователя.
Обрабатывает все сообщения, которые не обработаны другими обработчиками.
Реализует систему списания средств за использование бота и хранение истории сообщений.
"""

import math
import re
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
from services.holos_api import send_request_to_holos
from config import (
    TOKEN_PRICE, 
    MIN_REQUIRED_BALANCE, 
    INPUT_TOKEN_MULTIPLIER,
    OUTPUT_TOKEN_MULTIPLIER,
    HOLOS_DREAM_URL
)
from handlers.consultation_mode import get_end_consultation_keyboard
from handlers.onboarding import geocode_location  # Импортируем существующую функцию

router = Router()

# Функция для определения, содержит ли текст запрос на определение типа личности
def is_hd_type_request(text):
    patterns = [
        # Стандартные запросы о типе
        r"(?:определи|какой|узнать?|скажи|посмотри).{1,30}тип",
        r"тип\s+личности",
        
        # Запросы с использованием слов, связанных с типированием
        r"типиру[йя]",
        r"(?:про|за)типиру[йя]",
        r"(?:сделай|проведи|дай).{1,20}типирование",
        
        # Запросы на анализ
        r"(?:сделай|дай|проведи).{1,20}анализ",
        r"проанализиру[йя]",
        
        # Термины Human Design
        r"хьюман\s+дизайн",
        r"human\s+design",
        r"(?:определи|расскажи\s+о).{1,20}дизайн[еа]",
        r"генны[йе]\s+ключ[и]?",
        r"канал[ыа]?",
        r"профиль\s+\d/\d",
        r"(?:определи|тип\s+по)\s+авторитет[ау]?",
        r"стратеги[яю]",
        
        # Данные о рождении
        r"дата.{1,10}рождения",
        r"родил(?:ся|ась)",
        r"\d{4}-\d{2}-\d{2}.*\d{1,2}:\d{2}"
    ]
    
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in patterns)

# Функция для извлечения даты, времени и места рождения из текста
def extract_birth_info(text):
    # Ищем дату рождения (YYYY-MM-DD или DD.MM.YYYY)
    date_patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{2}\.\d{2}\.\d{4})"
    ]
    
    # Ищем время рождения (HH:MM)
    time_pattern = r"(\d{1,2}[:\.]\d{2})"
    
    # Ищем место рождения (предполагаем, что это слово с заглавной буквы после ключевых слов)
    place_patterns = [
        r"(?:место|город|родил(?:ся|ась) в)\s+([А-Я][а-яА-Я\-]+)",
        r"([А-Я][а-яА-Я\-]+)(?:\s+[а-яА-Я\-]+){0,2}$"
    ]
    
    # Ищем все совпадения
    date = None
    for pattern in date_patterns:
        date_match = re.search(pattern, text)
        if date_match:
            date = date_match.group(1)
            # Преобразуем DD.MM.YYYY в YYYY-MM-DD, если необходимо
            if "." in date:
                parts = date.split(".")
                if len(parts) == 3:
                    date = f"{parts[2]}-{parts[1]}-{parts[0]}"
            break
    
    time = None
    time_match = re.search(time_pattern, text)
    if time_match:
        time = time_match.group(1)
        # Заменяем точку на двоеточие, если необходимо
        time = time.replace(".", ":")
    
    place = None
    for pattern in place_patterns:
        place_match = re.search(pattern, text)
        if place_match:
            place = place_match.group(1)
            break
    
    return date, time, place

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
    
    # Проверяем, является ли сообщение запросом на определение типа личности
    is_hd_request = is_hd_type_request(message.text)
    needs_api_call = "через апи" in message.text.lower() or "через api" in message.text.lower()
    
    # Если это запрос на определение типа личности, обрабатываем его особым образом
    if is_hd_request:
        # Извлекаем дату, время и место рождения
        date, time, place = extract_birth_info(message.text)
        
        # Если не удалось извлечь всю необходимую информацию, запрашиваем у пользователя
        if not all([date, time, place]):
            missing_info = []
            if not date:
                missing_info.append("дату рождения (в формате ГГГГ-ММ-ДД)")
            if not time:
                missing_info.append("время рождения (в формате ЧЧ:ММ)")
            if not place:
                missing_info.append("место рождения")
            
            await message.answer(
                "Для определения типа личности через API мне не хватает следующей информации: " + 
                ", ".join(missing_info) + ". Пожалуйста, предоставьте эти данные."
            )
            return
        
        # Сообщаем пользователю, что начинаем анализ
        await message.answer("Определяю тип личности через API... Один момент.")
        
        try:
            # Получаем координаты по названию места с помощью существующей функции
            latitude, longitude, altitude = await geocode_location(place)
            
            # Формируем строку даты и времени
            date_str = f"{date} {time}"
            
            # Отправляем запрос к API Holos
            status_message = await message.answer("Отправляю запрос к API... Это может занять несколько секунд.")
            
            response_data = await send_request_to_holos(
                holos_url=HOLOS_DREAM_URL,
                date_str=date_str,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude
            )
            
            # Обрабатываем ответ
            if "error" in response_data:
                await status_message.edit_text(
                    f"Произошла ошибка при обращении к API: {response_data.get('error', 'Неизвестная ошибка')}"
                )
                return
            
            # Собираем данные пользователя в виде строки
            user_profile_info = (
                f"Дата рождения: {date}\n"
                f"Время рождения: {time}\n"
                f"Место рождения: {place}\n"
                f"Координаты: {latitude}, {longitude}, {altitude}\n"
                f"Данные API: {response_data}"
            )
            
            holos_data_combined = {
                "user_profile": user_profile_info,
                "api_response": response_data
            }
            
            # Сохраняем данные в состоянии для использования в будущих запросах
            await state.update_data(holos_response=holos_data_combined)
            
            # Генерируем ответ с помощью RAG
            expert_prompt = "Определи тип личности на основе предоставленных данных API. Это новый анализ через API, не используй предыдущие данные."
            
            # Получаем историю диалога
            messages_history = get_last_messages(user_id, 100)
            conversation_history = ""
            for msg in messages_history:
                if msg['is_summary']:
                    conversation_history += f"Краткое содержание предыдущего диалога: {msg['content']}\n\n"
                else:
                    prefix = "Пользователь: " if msg['sender'] == 'user' else "Бот: "
                    conversation_history += f"{prefix}{msg['content']}\n"
            
            expert_comment = answer_with_rag(
                expert_prompt,
                holos_data_combined,
                mode="free",
                conversation_history=conversation_history,
                max_tokens=1200
            )
            
            # Удаляем статусное сообщение
            await status_message.delete()
            
            # Сохраняем ответ бота в базу данных
            save_message(user_id, 'bot', expert_comment)
            
            # Отправляем ответ
            await message.answer(expert_comment, reply_markup=get_end_consultation_keyboard())
            return
                
        except Exception as e:
            await message.answer(f"Произошла ошибка при определении типа личности: {str(e)}")
            return
    
    # Если это обычный запрос, обрабатываем как раньше
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