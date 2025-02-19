import os
import re
import openai
from .pdf_data import get_pdf_content  # Теперь функция принимает путь к PDF
from config import OPENAI_API_KEY

CHAT_MODEL = "gpt-4o"  # или используйте ту модель, к которой есть доступ
openai.api_key = OPENAI_API_KEY

def load_gene_keys_text(holos_data: dict) -> str:
    """
    Из объекта holos_data извлекает номера генных ключей.
    Функция пытается найти значение в следующих вариантах:
      - holos_data["cross"]["crossnum"]
      - holos_data["crossnum"]
      - holos_data["cross\\"]["crossnum"]
    Если ни один из них не найден, то пытается найти их в holos_data["api_response"]["data"]["cross"]["crossnum"].
    Затем с помощью регулярного выражения извлекаются все числа (от 1 до 64),
    и для каждого формируется путь к файлу в папке "data" с именем вида:
         "<номер>-й_ГЕННЫЙ_КЛЮЧ_summary.pdf"
    Из этих файлов извлекается текст и объединяется в один блок.
    При этом выводится в консоль список используемых файлов и исходная строка с номерами ключей.
    """
    gene_text = ""
    keys = []
    crossnum_str = None

    # Попытка найти на верхнем уровне
    if "cross" in holos_data and isinstance(holos_data["cross"], dict):
        crossnum_str = holos_data["cross"].get("crossnum")
    if not crossnum_str and "crossnum" in holos_data:
        crossnum_str = holos_data["crossnum"]
    if not crossnum_str and "cross\\" in holos_data and isinstance(holos_data["cross\\"], dict):
        crossnum_str = holos_data["cross\\"].get("crossnum")
    # Если не найдено, попробуем вложенную структуру
    if not crossnum_str and "api_response" in holos_data:
        api_data = holos_data["api_response"].get("data", {})
        if "cross" in api_data and isinstance(api_data["cross"], dict):
            crossnum_str = api_data["cross"].get("crossnum")
    
    if not crossnum_str:
        print("Не найдены данные о генных ключах в holos_data.")
        return "[Нет данных о генных ключах]"
    
    print("Исходная строка с номерами генных ключей:", crossnum_str)
    
    # Извлекаем все последовательности цифр длиной 1-2 символа
    found_numbers = re.findall(r"\d{1,2}", crossnum_str)
    keys = [str(int(num)) for num in found_numbers if 1 <= int(num) <= 64]
    
    used_files = []
    for key in keys:
        # Используем расширение .pdf в нижнем регистре
        file_path = f"data_summaries/{key}-й_ГЕННЫЙ_КЛЮЧ_summary.pdf"
        used_files.append(file_path)
        try:
            content = get_pdf_content(file_path)
            gene_text += f"\n--- Описание генного ключа {key} ---\n{content}\n"
        except Exception as e:
            gene_text += f"\n--- Не удалось загрузить описание для генного ключа {key}: {e} ---\n"
    print("Используемые файлы для описания генных ключей:")
    for file in used_files:
        print(file)
    return gene_text

def answer_with_rag(query: str, holos_data: dict, mode: str = "free", conversation_history: str = "", max_tokens: int = 1200) -> str:
    """
    Формирует prompt для ChatGPT, используя:
      - Данные с сайта Holos (из API и базы),
      - Описания генных ключей, извлеченные из PDF-файлов в папке "data".
        Для каждого генного ключа, найденного в holos_data (через поле "cross" или "crossnum"),
        используется файл с именем вида "<номер>-й_ГЕННЫЙ_КЛЮЧ.pdf".
      - Историю диалога (conversation_history).

    Если mode=="4_aspects", ChatGPT должен:
      1. На основе предоставленных данных (сведения о дате, времени и месте рождения, полученные через API)
         определить тип личности пользователя.
      2. В первой строке ответа явно указать: "Ваш тип личности: <тип>" с кратким описанием его особенностей.
      3. Затем дать обзор по типу личности с особым акцентом на описание генных ключей.
         Ответ не должен превышать 350 слов.
    
    Если mode=="free", ответ формируется свободно по теме (не длиннее ~250 слов).

    Параметр max_tokens определяет максимальное число токенов в ответе.
    """
    holos_text = f"Данные с сайта Holos:\n{holos_data}" if holos_data else "[Нет данных]"
    
    gene_keys_text = load_gene_keys_text(holos_data)
    
    history_text = f"История диалога:\n{conversation_history}" if conversation_history else ""
    
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
    
    user_prompt = f"""
--- Данные пользователя (БД и API) ---
{holos_text}

--- Описание генных ключей (файлы из папки data) ---
{gene_keys_text}

--- История диалога ---
{history_text}

Вопрос: {query}
"""
    print("ПРОМПТ ДЛЯ CHATGPT:")
    print(user_prompt)
    
    response = openai.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.7
    )
    return response.choices[0].message.content
