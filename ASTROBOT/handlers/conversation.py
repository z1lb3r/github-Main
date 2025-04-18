"""
Обработчик обычных сообщений пользователя.
Обрабатывает все сообщения, которые не обработаны другими обработчиками.
Реализует систему списания средств за использование бота и хранение истории сообщений.
Фокусируется на помощи в отношениях с другими людьми.
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

# Функция для определения, содержит ли текст запрос на определение типа личности или отношений
def is_hd_type_request(text):
    """
    Определяет, является ли запрос пользователя запросом о типе личности или отношениях.
    
    Args:
        text (str): Текст запроса
        
    Returns:
        bool: True, если это запрос о типе личности или отношениях
    """
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
        r"\d{4}-\d{2}-\d{2}.*\d{1,2}:\d{2}",
        
        # Запросы об отношениях
        r"(?:отношени[йяе]|общени[йяе])\s+с",
        r"(?:муж|жена|партнер|супруг|возлюбленн|колле|начальни|родите|ребен|дет|друг)",
        r"(?:семь[яеи]|работ[ае]|дружб[ае]|любов|романти|брак)",
        r"(?:как\s+(?:общаться|говорить|вести себя))\s+с",
        r"(?:переговор|конфликт|спор|разногласи|понимани)"
    ]
    
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in patterns)

# Функция для извлечения даты, времени и места рождения из текста
def extract_birth_info(text):
    """
    Извлекает дату, время и место рождения из текста.
    
    Args:
        text (str): Текст запроса
        
    Returns:
        tuple: (дата, время, место)
    """
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

# Функция для извлечения информации об отношениях из текста
def extract_relationship_info(text):
    """
    Извлекает информацию об отношениях из текста.
    
    Args:
        text (str): Текст запроса
        
    Returns:
        dict: Словарь с информацией о типе отношений и контексте
    """
    text_lower = text.lower()
    
    # Словарь для хранения информации
    relationship_info = {
        "type": None,  # тип отношений: family, romantic, work, friends
        "person": None,  # с кем: mother, boss, partner и т.д.
        "context": None,  # контекст: conflict, communication, negotiation
    }
    
    # Проверяем тип отношений
    if any(word in text_lower for word in ["семь", "родител", "мам", "пап", "муж", "жен", "брат", "сестр", "дети", "ребенок", "сын", "дочь"]):
        relationship_info["type"] = "family"
    elif any(word in text_lower for word in ["любов", "романтич", "партнер", "отношения", "брак", "свидани", "развод"]):
        relationship_info["type"] = "romantic"
    elif any(word in text_lower for word in ["работ", "коллег", "начальник", "босс", "карьер", "бизнес", "сотрудник"]):
        relationship_info["type"] = "work"
    elif any(word in text_lower for word in ["друг", "подруг", "приятел", "знаком", "компани"]):
        relationship_info["type"] = "friends"
    
    # Определяем человека, о котором идет речь
    person_patterns = {
        "mother": r"(?:мам|матер)",
        "father": r"(?:пап|отц|отец)",
        "partner": r"(?:партнер|муж|жен|супруг)",
        "boss": r"(?:начальник|босс|руководител)",
        "colleague": r"(?:коллег|сотрудник)",
        "friend": r"(?:друг|подруг|приятел)",
        "child": r"(?:ребенок|ребенк|дет|сын|доч)"
    }
    
    for person, pattern in person_patterns.items():
        if re.search(pattern, text_lower):
            relationship_info["person"] = person
            break
    
    # Определяем контекст общения
    context_patterns = {
        "conflict": r"(?:конфликт|ссор|спор|ругань|непониман)",
        "communication": r"(?:общен|коммуникац|разговор|диалог)",
        "negotiation": r"(?:переговор|договор|обсужден)",
        "boundaries": r"(?:границ|личное|пространств)"
    }
    
    for context, pattern in context_patterns.items():
        if re.search(pattern, text_lower):
            relationship_info["context"] = context
            break
    
    return relationship_info

@router.message()
async def conversation_handler(message: Message, state: FSMContext):
    """
    Обработчик обычных сообщений пользователя.
    Генерирует ответы с фокусом на помощь в отношениях, отслеживает историю диалога,
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
            "с детальным анализом и получить конкретные советы по улучшению отношений, "
            "пожалуйста, выберите 'Начать консультацию' в главном меню."
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
            f"Ваш текущий баланс: {balance:.0f} кредитов\n"
            f"Минимальный баланс для консультации: {MIN_REQUIRED_BALANCE:.0f} кредитов\n\n"
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
    
    # Извлекаем информацию об отношениях, если она присутствует
    relationship_info = extract_relationship_info(message.text)
    
    # Проверяем, является ли сообщение запросом на определение типа личности
    is_hd_request = is_hd_type_request(message.text)
    needs_api_call = "через апи" in message.text.lower() or "через api" in message.text.lower()
    
    # Если это запрос на определение типа личности, обрабатываем его особым образом
    if is_hd_request and needs_api_call:
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
                "Для определения типа личности мне не хватает следующей информации: " + 
                ", ".join(missing_info) + ". Пожалуйста, предоставьте эти данные, чтобы я мог помочь вам с советами по улучшению отношений."
            )
            return
        
        # Сообщаем пользователю, что начинаем анализ
        await message.answer("Определяю ваш тип личности... Один момент.")
        
        try:
            # Получаем координаты по названию места с помощью существующей функции
            latitude, longitude, altitude = await geocode_location(place)
            
            # Формируем строку даты и времени
            date_str = f"{date} {time}"
            
            # Отправляем запрос к API Holos
            status_message = await message.answer("Получаю данные для анализа... Это может занять несколько секунд.")
            
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
                    f"Произошла ошибка при получении данных: {response_data.get('error', 'Неизвестная ошибка')}"
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
            
            # Добавляем информацию об отношениях, если она есть
            relationship_prompt = ""
            if relationship_info["type"]:
                relationship_type_map = {
                    "family": "семейных отношениях",
                    "romantic": "романтических отношениях",
                    "work": "рабочих отношениях",
                    "friends": "дружеских отношениях"
                }
                relationship_prompt = f" Пользователь интересуется советами о {relationship_type_map.get(relationship_info['type'], 'отношениях')}."
                if relationship_info["person"]:
                    person_map = {
                        "mother": "матерью",
                        "father": "отцом",
                        "partner": "партнером",
                        "boss": "начальником",
                        "colleague": "коллегами",
                        "friend": "друзьями",
                        "child": "детьми"
                    }
                    relationship_prompt += f" Конкретно об отношениях с {person_map.get(relationship_info['person'], 'людьми')}."
                
                if relationship_info["context"]:
                    context_map = {
                        "conflict": "разрешении конфликтов",
                        "communication": "улучшении коммуникации",
                        "negotiation": "ведении переговоров",
                        "boundaries": "установлении границ"
                    }
                    relationship_prompt += f" В контексте {context_map.get(relationship_info['context'], 'общения')}."
            
            # Генерируем ответ с помощью RAG
            expert_prompt = f"Определи тип личности на основе предоставленных данных, используя простой язык. Объясни 1-2 ключевые особенности, а затем дай конкретные практические советы по улучшению отношений с другими людьми.{relationship_prompt}"
            
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
            await message.answer(f"Произошла ошибка при анализе: {str(e)}")
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
    
    # Добавляем информацию об отношениях, если она есть
    relationship_prompt = ""
    if relationship_info["type"]:
        relationship_type_map = {
            "family": "семейных отношениях",
            "romantic": "романтических отношениях",
            "work": "рабочих отношениях",
            "friends": "дружеских отношениях"
        }
        relationship_prompt = f" Пользователь интересуется советами о {relationship_type_map.get(relationship_info['type'], 'отношениях')}."
        if relationship_info["person"]:
            person_map = {
                "mother": "матерью",
                "father": "отцом",
                "partner": "партнером",
                "boss": "начальником",
                "colleague": "коллегами",
                "friend": "друзьями",
                "child": "детьми"
            }
            relationship_prompt += f" Конкретно об отношениях с {person_map.get(relationship_info['person'], 'людьми')}."
        
        if relationship_info["context"]:
            context_map = {
                "conflict": "разрешении конфликтов",
                "communication": "улучшении коммуникации",
                "negotiation": "ведении переговоров",
                "boundaries": "установлении границ"
            }
            relationship_prompt += f" В контексте {context_map.get(relationship_info['context'], 'общения')}."
    
    # Если запрос неясен, добавляем инструкцию запросить уточнение
    clarity_instruction = ""
    if not relationship_info["type"] and not is_hd_request:
        clarity_instruction = " Если запрос неясен или слишком общий, вежливо задай 1-2 уточняющих вопроса о том, с какими отношениями пользователь хотел бы помощи (семья, романтика, работа, друзья)."
    
    # Формируем модифицированный запрос пользователя с учетом контекста отношений
    modified_query = message.text + relationship_prompt + clarity_instruction
    
    # Генерируем ответ с помощью RAG
    answer = answer_with_rag(
        modified_query,  # Модифицированный запрос пользователя
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