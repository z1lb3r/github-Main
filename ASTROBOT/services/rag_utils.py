"""
Сервис для генерации ответов с использованием RAG (Retrieval-Augmented Generation).
Использует данные из API Holos и описания генных ключей для формирования ответов.
"""

import os
import re
import openai
import tiktoken
from .pdf_data import get_pdf_content
from config import OPENAI_API_KEY

# Модель ChatGPT для генерации ответов
CHAT_MODEL =  "gpt-4.1-mini"   # "gpt-4.1-2025-04-14"
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

def answer_with_rag(query: str, holos_data: dict, mode: str = "free", conversation_history: str = "", max_tokens: int = 2800, type_shown: bool = False) -> str:
    """
    Формирует ответ на запрос пользователя с использованием RAG.
    
    Args:
        query (str): Запрос пользователя
        holos_data (dict): Данные из API Holos
        mode (str): Режим ответа ("free" - свободный ответ)
        conversation_history (str): История диалога
        max_tokens (int): Максимальное количество токенов в ответе
        type_shown (bool): Флаг, указывающий, был ли уже показан тип личности пользователю
        
    Returns:
        str: Сгенерированный ответ
    """
    print(f"[DEBUG] answer_with_rag вызван с запросом: '{query[:50]}...'")
    print(f"[DEBUG] Длина истории диалога: {len(conversation_history)} символов")
    print(f"[DEBUG] Тип личности уже показан: {type_shown}")
    
    # Проверяем, содержит ли запрос явную просьбу указать тип личности
    type_request_keywords = ["мой тип", "тип личности", "какой у меня тип", "определи мой тип", "какой я тип"]
    is_type_request = any(keyword in query.lower() for keyword in type_request_keywords)
    
    # Проверяем, содержит ли запрос указание на повторное обращение
    is_repeat_query = "повторное обращение" in query.lower() or "не определяй тип" in query.lower()
    print(f"[DEBUG] Запрос определен как {'ПОВТОРНОЕ обращение' if is_repeat_query else 'НОВОЕ обращение'}")
    
    # Формируем текст с данными Holos
    holos_text = f"Данные с сайта Holos:\n{holos_data}" if holos_data else "[Нет данных]"
    
    # Загружаем описания генных ключей
    gene_keys_text = load_gene_keys_text(holos_data)
    
    # Добавляем историю диалога
    history_text = f"История диалога:\n{conversation_history}" if conversation_history else ""
    
    # Определяем, является ли это первым сообщением и нужно ли показывать тип
    is_first_message = "Пользователь:" not in conversation_history and "Бот:" not in conversation_history
    should_show_type = (is_first_message and not type_shown) or is_type_request
    
    # Специальные инструкции в зависимости от типа запроса
    if (is_repeat_query or type_shown) and not is_type_request:
        first_message_instruction = (
            "ВАЖНО: НЕ ОПРЕДЕЛЯЙ и НЕ УПОМИНАЙ тип личности в начале ответа. "
            "Пользователь уже знает свой тип личности. Отвечай на вопрос напрямую, не повторяя тип личности. "
            "Ты — консультант (МУЖЧИНА) по Human Design, ВСЕГДА используй мужской род в своих ответах. "
            "Никогда не начинай ответ с фразы 'Ваш тип личности' или подобной."
        )
    else:
        # Модифицируем инструкцию для первого сообщения или при явном запросе типа
        first_message_instruction = (
            "Это первое сообщение в диалоге. Кратко укажи тип личности пользователя и дай очень краткое описание "
            "основных характеристик этого типа (1-2 абзаца максимум). НЕ ПРЕДЛАГАЙ помощь и советы сразу - "
            "строго следуй тексту пользовательского запроса после определения типа личности. "
            "Ты — консультант (МУЖЧИНА) по Human Design, ВСЕГДА используй мужской род в своих ответах. "
            "После этого первого сообщения НИКОГДА не повторяй тип личности, если пользователь явно тебя об этом не просит."
            if should_show_type else 
            "НЕ УКАЗЫВАЙ тип личности в начале. Пользователь уже знает свой тип личности. "
            "Ты — консультант (МУЖЧИНА) по Human Design, ВСЕГДА используй мужской род в своих ответах. "
            "Никогда не начинай ответ с фразы 'Ваш тип личности' или подобной."
        )
    
    # Модифицированный системный промпт с фокусом только на определении типа личности
    system_msg = (
    f"{first_message_instruction}\n\n"
    
    "Ты — консультант (МУЖЧИНА) по Human Design, который определяет тип личности на основе данных о дате, времени и месте рождения. "
    "ВСЕГДА используй грамматические формы мужского рода - например, говори 'я рад', 'я готов помочь', а не 'я рада', 'я готова помочь'. "
    "СТРОГОЕ ПРАВИЛО: Ты НИКОГДА не должен указывать или упоминать тип личности пользователя в начале сообщения, "
    "КРОМЕ СЛЕДУЮЩИХ СЛУЧАЕВ: 1) Это самое первое сообщение в консультации (при этом флаг type_shown = false) "
    "ИЛИ 2) Пользователь ЯВНО просит указать его тип личности.\n\n"

    "ОЧЕНЬ ВАЖНО: Читай и учитывай всю историю диалога. Не повторяй информацию, которая уже была предоставлена.\n\n"

    "ПРАВИЛА ОТВЕТА:\n"
    "1. Используй простые, понятные слова и избегай сложных терминов Human Design без пояснения.\n"
    "2. При первом обращении через консультацию или при явном запросе - укажи тип личности и очень кратко опиши его характеристики.\n"
    "3. ВО ВСЕХ ДРУГИХ СЛУЧАЯХ - НИКОГДА НЕ УПОМИНАЙ и НЕ ОБСУЖДАЙ тип личности в начале ответа.\n"
    "4. Всегда конкретно отвечай на вопрос пользователя без лишних отступлений.\n\n"

    "ОПРЕДЕЛЕНИЕ ТИПА ЛИЧНОСТИ (ТОЛЬКО ПРИ ПЕРВОМ СООБЩЕНИИ ИЛИ ЯВНОМ ЗАПРОСЕ):\n"
    "• Указывай тип личности в формате: \"Тип личности: [тип], профиль [профиль], [авторитет] авторитет\"\n"
    "• Давай очень краткое описание характеристик типа (1-2 абзаца максимум)\n"
    "• Если запрос содержит дополнительный текст, который должен следовать после определения типа, "
    "то четко следуй этому тексту без добавления собственных фраз и предложений.\n\n"

    "Всегда стремись быть понятным и четким."
)
    
    # Формируем запрос для GPT
    user_prompt = f"""
--- Данные пользователя (БД и API) ---
{holos_text}

--- Описание генных ключей (файлы из папки data) ---
{gene_keys_text}

--- История диалога ---
{history_text}

Текущий вопрос пользователя: {query}
"""
    
    # Выводим промпт для отладки (можно закомментировать в продакшн)
    print("[DEBUG] СИСТЕМНЫЙ ПРОМПТ (первые 500 символов):")
    print(system_msg[:500] + "...")
    
    print("[DEBUG] ПОЛЬЗОВАТЕЛЬСКИЙ ПРОМПТ (первые 500 символов):")
    print(user_prompt[:500] + "...")
    
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
    print(f"[DEBUG] Создана суммаризация: {summary[:100]}...")
    return summary