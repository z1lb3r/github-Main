"""
Сервис для генерации ответов с использованием RAG (Retrieval-Augmented Generation).
Использует данные из API Holos и описания генных ключей для формирования ответов.
"""

import os
import re
import openai
from .pdf_data import get_pdf_content
from config import OPENAI_API_KEY

# Модель ChatGPT для генерации ответов
CHAT_MODEL = "gpt-4o"

# Устанавливаем API ключ для OpenAI
openai.api_key = OPENAI_API_KEY

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
        file_path = f"data_summaries/{key}-й_ГЕННЫЙ_КЛЮЧ_summary.pdf"
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

def answer_with_rag(query: str, holos_data: dict, mode: str = "free", conversation_history: str = "", max_tokens: int = 1200) -> str:
    """
    Формирует ответ на запрос пользователя с использованием RAG.
    
    Args:
        query (str): Запрос пользователя
        holos_data (dict): Данные из API Holos
        mode (str): Режим ответа ("4_aspects" - анализ по 4 аспектам, "free" - свободный ответ)
        conversation_history (str): История диалога
        max_tokens (int): Максимальное количество токенов в ответе
        
    Returns:
        str: Сгенерированный ответ
    """
    # Формируем текст с данными Holos
    holos_text = f"Данные с сайта Holos:\n{holos_data}" if holos_data else "[Нет данных]"
    
    # Загружаем описания генных ключей
    gene_keys_text = load_gene_keys_text(holos_data)
    
    # Добавляем историю диалога
    history_text = f"История диалога:\n{conversation_history}" if conversation_history else ""
    
    # Выбираем системное сообщение в зависимости от режима
    if mode == "4_aspects":
        system_msg = (
            "Ты — интеллектуальный чат-бот, работающий на принципах рефлектора 5/1 из системы Дизайна Человека и генетических ключей. "
            "Используя предоставленные данные, включая сведения о дате, времени и месте рождения пользователя (из API), "
            "а также описания генных ключей, прочитанные из PDF-файлов из папки \"data_summaries\", определи тип личности пользователя. "
            "В первой строке ответа обязательно укажи: 'Ваш тип личности: <тип>' с кратким описанием его особенностей. "
            "Затем дай обзор по типу личности с особым акцентом на описание генных ключей. "
            "Не используй фразы типа 'я не знаю' или 'не являюсь экспертом'. "
            "Ответ должен быть не длиннее 350 слов."
        )
    else:
        system_msg = (
            "Ты — эксперт по Human Design и эзотерике. "
            "Ответь на вопрос пользователя, используя предоставленные данные, историю диалога и описания генных ключей. "
            "Ответ должен быть полезным, информативным и не длиннее 250 слов."
        )
    
    # Формируем запрос для GPT
    user_prompt = f"""
--- Данные пользователя (БД и API) ---
{holos_text}

--- Описание генных ключей (файлы из папки data) ---
{gene_keys_text}

--- История диалога ---
{history_text}

Вопрос: {query}
"""
    
    # Выводим промпт для отладки
    print("ПРОМПТ ДЛЯ CHATGPT:")
    print(user_prompt)
    
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
    
    # Возвращаем сгенерированный ответ
    return response.choices[0].message.content