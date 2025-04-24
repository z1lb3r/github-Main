"""
Сервис для генерации ответов с использованием RAG (Retrieval-Augmented Generation).
Использует данные из API Holos и описания генных ключей для формирования ответов.
"""

import os
import re
import openai
import tiktoken
import json
from .pdf_data import get_pdf_content
from config import OPENAI_API_KEY

# Модель ChatGPT для генерации ответов
CHAT_MODEL =  "gpt-4.1-mini" # "ft:gpt-4o-2024-08-06:personal::BDAbtw7T"  "gpt-4.1-mini"    "gpt-4.1-2025-04-14"
# Модель для подсчета токенов
ENCODING_MODEL = "cl100k_base"  # Энкодинг для GPT-4

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Устанавливаем API ключ для OpenAI
openai.api_key = OPENAI_API_KEY

def count_tokens(text: str) -> int:
    """
    Подсчитывает количество токенов в тексте.
    
    Args:
        text (str): Текст для подсчета токенов
        
    Returns:
        int: Количество токенов
    """
    try:
        encoding = tiktoken.get_encoding(ENCODING_MODEL)
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Ошибка при подсчете токенов: {str(e)}")
        # Если не удалось использовать tiktoken, используем приблизительный подсчет
        # В среднем 1 токен ~ 4 символа для английского текста
        # и ~2-3 символа для русского текста
        words = text.split()
        return len(words) * 1.5  # Примерная оценка

def load_gene_keys_text(holos_data: dict) -> str:
    """
    Извлекает номера генных ключей из данных Holos и загружает их описания из PDF-файлов.
    
    Args:
        holos_data (dict): Данные, полученные из API Holos
        
    Returns:
        str: Текст с описаниями генных ключей
    """
    gene_text = ""
    keys = []
    crossnum_str = None

    # Поиск номеров генных ключей в данных Holos
    # Проверяем разные варианты расположения данных в JSON
    
    # Вариант 1: Прямой доступ к полю cross/crossnum
    if isinstance(holos_data, dict):
        if "cross" in holos_data and isinstance(holos_data["cross"], dict):
            crossnum_str = holos_data["cross"].get("crossnum")
        
        # Вариант 2: Поле crossnum на верхнем уровне
        if not crossnum_str and "crossnum" in holos_data:
            crossnum_str = holos_data["crossnum"]
        
        # Вариант 3: Поле cross\\/crossnum (с экранированием)
        if not crossnum_str and "cross\\" in holos_data and isinstance(holos_data["cross\\"], dict):
            crossnum_str = holos_data["cross\\"].get("crossnum")
        
        # Вариант 4: Вложенная структура api_response/data/cross/crossnum
        if not crossnum_str and "api_response" in holos_data:
            api_data = holos_data["api_response"].get("data", {})
            if "cross" in api_data and isinstance(api_data["cross"], dict):
                crossnum_str = api_data["cross"].get("crossnum")

    if not crossnum_str:
        print("Не найдены данные о генных ключах в holos_data.")
        return "[Нет данных о генных ключах]"
    
    print("Исходная строка с номерами генных ключей:", crossnum_str)
    
    # Извлекаем номера ключей (числа от 1 до 64)
    found_numbers = re.findall(r"\d{1,2}", crossnum_str)
    keys = [str(int(num)) for num in found_numbers if 1 <= int(num) <= 64]
    
    # Загружаем описания для каждого ключа
    used_files = []
    for key in keys:
        file_path = os.path.join(BASE_DIR, "data_summaries", f"{key}-й_ГЕННЫЙ_КЛЮЧ_summary.pdf")
        used_files.append(file_path)
        
        try:
            # Извлекаем текст из PDF-файла
            content = get_pdf_content(file_path)
            gene_text += f"\n--- Описание генного ключа {key} ---\n{content}\n"
        except Exception as e:
            gene_text += f"\n--- Не удалось загрузить описание для генного ключа {key}: {e} ---\n"
    
    # Выводим список используемых файлов (для отладки)
    print("Используемые файлы для описания генных ключей:")
    for file in used_files:
        print(file)
    
    return gene_text

def answer_with_rag(query: str, holos_data: dict, mode: str = "free", conversation_history: str = "", max_tokens: int = 2800) -> str:
    """
    Формирует ответ на запрос пользователя с использованием RAG.
    
    Args:
        query (str): Запрос пользователя
        holos_data (dict): Данные из API Holos
        mode (str): Режим ответа ("free" - свободный ответ)
        conversation_history (str): История диалога
        max_tokens (int): Максимальное количество токенов в ответе
        
    Returns:
        str: Сгенерированный ответ
    """
    print(f"[DEBUG] answer_with_rag вызван с запросом: '{query[:50]}...'")
    print(f"[DEBUG] Длина истории диалога: {len(conversation_history)} символов")
    
    # Проверяем, есть ли данные API для печати
    has_holos_data = isinstance(holos_data, dict) and ('api_response' in holos_data or (isinstance(holos_data.get('api_response'), dict)))
    
    # Вывод полных данных API для анализа в отладочный режим
    if has_holos_data:
        print("=== ПОЛНЫЕ ДАННЫЕ ОТ API HOLOS (Отладка) ===")
        if 'api_response' in holos_data:
            print(json.dumps(holos_data['api_response'], indent=4))
        else:
            print(json.dumps(holos_data, indent=4))
        print("=== КОНЕЦ ОТЛАДОЧНЫХ ДАННЫХ ===")
    
    # Определяем, является ли запрос о типе личности
    is_type_request = any(keyword in query.lower() for keyword in [
        "мой тип", "тип личности", "какой у меня тип", 
        "определи мой тип", "какой я тип", "узнать тип", "типирова"
    ])
    
    # Проверяем, запрашивает ли пользователь информацию о генных ключах
    is_gene_keys_request = any(keyword in query.lower() for keyword in [
        "генны", "ключ", "gate", "гейт", "канал", "ворота"
    ])
    
    # Первое сообщение определяем по пустой истории диалога
    is_first_message = not conversation_history.strip()
    
    # Формируем текст с данными Holos только если это запрос типа, запрос о генных ключах или первое сообщение
    include_full_data = is_type_request or is_gene_keys_request or is_first_message
    
    if include_full_data and has_holos_data:
        holos_text = f"Данные с сайта Holos:\n{holos_data}"
    else:
        holos_text = "Базовая информация о профиле сохранена в системе."
    
    # Загружаем описания генных ключей только при необходимости
    if include_full_data and has_holos_data:
        gene_keys_text = load_gene_keys_text(holos_data)
    else:
        gene_keys_text = "Информация о генных ключах доступна по запросу."
    
    # Добавляем историю диалога
    history_text = f"История диалога:\n{conversation_history}" if conversation_history else ""
    
    # Системный промпт с четкими инструкциями
    if is_type_request:
        first_message_instruction = (
            "Определи тип личности пользователя по Human Design в начале ответа. "
            "Кратко укажи тип, профиль и авторитет, затем дай очень краткое описание "
            "основных характеристик (1-2 абзаца максимум). После этого ответь на запрос пользователя. "
            "Ты — консультант (МУЖЧИНА) по Human Design, ВСЕГДА используй мужской род в своих ответах."
        )
    else:
        first_message_instruction = (
            "Отвечай на вопрос пользователя о Human Design, не упоминая тип личности в начале ответа, "
            "если пользователь явно не запрашивает этот тип. "
            "Ты — консультант (МУЖЧИНА) по Human Design, ВСЕГДА используй мужской род в своих ответах."
        )
    
    system_msg = (
        f"{first_message_instruction}\n\n"
        
        "ОЧЕНЬ ВАЖНО: Читай и учитывай всю историю диалога. Не повторяй информацию, которая уже была предоставлена.\n\n"
        
        "ПРАВИЛА ОБЩЕНИЯ:\n"
        "1. Используй простые, понятные слова и избегай сложных терминов Human Design без пояснения.\n"
        "2. Давай конкретные, практические советы вместо абстрактных рассуждений.\n"
        "3. Если не понимаешь запрос или нужны дополнительные детали — прямо спрашивай пользователя.\n"
        "4. ЗАПРЕЩЕНО начинать ответ с фразы 'Ваш тип личности' или подобной, если это не явный запрос типа.\n"
        "5. Задавай целенаправленные вопросы, чтобы понять ситуацию пользователя и дать точные рекомендации.\n"
        "6. Всегда приводи примеры, как именно пользователь может применить советы в конкретных ситуациях.\n\n"
        
        "Всегда стремись быть понятным и четким."
    )
    
    # Формируем запрос для GPT с условным включением данных
    user_prompt = ""
    
    # Добавляем данные Holos только если нужны полные данные
    if include_full_data and has_holos_data:
        user_prompt += f"--- Данные пользователя (БД и API) ---\n{holos_text}\n\n"
        user_prompt += f"--- Описание генных ключей (файлы из папки data) ---\n{gene_keys_text}\n\n"
    
    # Всегда добавляем историю диалога и текущий запрос
    user_prompt += f"--- История диалога ---\n{history_text}\n\n"
    user_prompt += f"Текущий вопрос пользователя: {query}"
    
    # Выводим промпт для отладки (можно закомментировать в продакшн)
    print("[DEBUG] СИСТЕМНЫЙ ПРОМПТ (первые 500 символов):")
    print(system_msg[:500] + "...")
    
    print("[DEBUG] ПОЛЬЗОВАТЕЛЬСКИЙ ПРОМПТ (первые 500 символов):")
    print(user_prompt[:500] + "...")

    system_tokens = count_tokens(system_msg)
    user_tokens = count_tokens(user_prompt)
    total_input_tokens = system_tokens + user_tokens

    print(f"[ТОКЕНЫ] Запрос к LLM: системный промпт {system_tokens} + пользовательский промпт {user_tokens} = {total_input_tokens} токенов")
    
    # Отправляем запрос к ChatGPT
    response = openai.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.7
    )
    
    answer_content = response.choices[0].message.content
    output_tokens = count_tokens(answer_content)
    print(f"[ТОКЕНЫ] Ответ от LLM: {output_tokens} токенов")
    print(f"[ТОКЕНЫ] Итого: вход {total_input_tokens} / выход {output_tokens} = {total_input_tokens + output_tokens} токенов")
    print(f"[DEBUG] Получен ответ от модели (первые 100 символов): {answer_content[:100]}...")
    
    # Возвращаем сгенерированный ответ
    return answer_content
    print(f"[DEBUG] Получен ответ от модели (первые 100 символов): {answer_content[:100]}...")
    
    # Возвращаем сгенерированный ответ
    return answer_content


def summarize_messages(messages: list, max_tokens: int = 500) -> str:
    """
    Суммаризирует набор сообщений.
    
    Args:
        messages (list): Список сообщений для суммаризации
        max_tokens (int): Максимальная длина суммаризации
        
    Returns:
        str: Краткое содержание сообщений
    """
    print(f"[DEBUG] Суммаризация {len(messages)} сообщений с моделью {CHAT_MODEL}")
    
    # Формируем диалог для суммаризации
    conversation = ""
    for msg in messages:
        prefix = "Пользователь: " if msg['sender'] == 'user' else "Бот: "
        conversation += f"{prefix}{msg['content']}\n\n"
    
    # Запрос к OpenAI для суммаризации
    print(f"[DEBUG] Отправляем запрос на суммаризацию к модели: {CHAT_MODEL}")
    
    response = openai.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "Ты - помощник, который кратко суммирует диалоги. Создай краткое резюме диалога, сохраняя важные детали и контекст."},
            {"role": "user", "content": f"Суммаризируй этот диалог между пользователем и ботом Human Design. Сохрани ключевую информацию о типе личности пользователя и важные темы обсуждения:\n\n{conversation}"}
        ],
        max_tokens=max_tokens,
        temperature=0.7
    )
    
    summary = response.choices[0].message.content
    print(f"[DEBUG] Создана суммаризация: {summary[:50]}...")
    return summary