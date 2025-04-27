"""
Сервис для генерации ответов с использованием RAG (Retrieval-Augmented Generation).
Использует данные из API Holos и описания генных ключей для формирования ответов.
"""

import os
import re
import openai
import tiktoken
import json
from logger import services_logger as logger
from logger import log_tokens, log_api_request, log_api_response, log_api_error, log_debug
from .pdf_data import get_pdf_content
from config import OPENAI_API_KEY, OPENAI_API_KEYS

# Модель ChatGPT для генерации ответов
CHAT_MODEL = "gpt-4.1-mini" # "ft:gpt-4o-2024-08-06:personal::BDAbtw7T"  "gpt-4.1-mini"    "gpt-4.1-2025-04-14"
# Модель для подсчета токенов
ENCODING_MODEL = "cl100k_base"  # Энкодинг для GPT-4

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Класс для управления API ключами по круговой стратегии
class APIKeyManager:
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.current_index = 0
        self.total_keys = len(api_keys)
        self.usage_count = {i: 0 for i in range(len(api_keys))}  # Счетчик использования каждого ключа
        self.total_requests = 0
        logger.info(f"Инициализирован менеджер ключей с {self.total_keys} ключами")
        
    def get_next_key(self):
        """Возвращает следующий ключ по круговой стратегии"""
        key_index = self.current_index
        key = self.api_keys[key_index]
        
        # Скрываем большую часть ключа для безопасности логирования
        masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "короткий_ключ"
        
        # Увеличиваем счетчик использования текущего ключа
        self.usage_count[key_index] += 1
        self.total_requests += 1
        
        # Выводим детальную информацию об использовании ключа
        logger.debug(f"Запрос #{self.total_requests}: Используется ключ #{key_index+1}/{self.total_keys} ({masked_key})")
        logger.debug(f"Статистика использования ключей: {self.usage_count}")
        
        # Переходим к следующему ключу для следующего запроса
        self.current_index = (self.current_index + 1) % self.total_keys
        
        return key
    
    def handle_error(self, error):
        """Обрабатывает ошибки API и переключается на следующий ключ при необходимости"""
        # Проверяем, связана ли ошибка с превышением лимитов
        error_str = str(error)
        rate_limit_errors = ["rate_limit", "capacity", "quota_exceeded", "maximum_context_length_exceeded"]
        
        if any(err_type in error_str.lower() for err_type in rate_limit_errors):
            failed_key_index = (self.current_index - 1) % self.total_keys
            logger.warning(f"Превышение лимитов для ключа #{failed_key_index+1}: {error_str}. Переключаемся на следующий ключ.")
            return self.get_next_key()
        else:
            # Если ошибка не связана с лимитами, пробрасываем её дальше
            raise error
    
    def get_usage_statistics(self):
        """Возвращает статистику использования ключей в удобном для чтения формате"""
        stats = []
        for i in range(self.total_keys):
            key = self.api_keys[i]
            masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "короткий_ключ"
            count = self.usage_count[i]
            percentage = (count / self.total_requests * 100) if self.total_requests > 0 else 0
            stats.append(f"Ключ #{i+1} ({masked_key}): {count} запросов ({percentage:.1f}%)")
        
        return "\n".join(stats)

# Создаем экземпляр менеджера ключей
key_manager = APIKeyManager(OPENAI_API_KEYS)

# Начальный ключ
openai.api_key = key_manager.get_next_key()

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
        logger.error(f"Ошибка при подсчете токенов: {str(e)}")
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

    # Нужно использовать корневую директорию проекта, а не директорию services
    PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
        logger.warning("Не найдены данные о генных ключах в holos_data.")
        return "[Нет данных о генных ключах]"
    
    logger.debug(f"Исходная строка с номерами генных ключей: {crossnum_str}")
    
    # Извлекаем номера ключей (числа от 1 до 64)
    found_numbers = re.findall(r"\d{1,2}", crossnum_str)
    keys = [str(int(num)) for num in found_numbers if 1 <= int(num) <= 64]
    
    # Загружаем описания для каждого ключа
    used_files = []
    for key in keys:
        file_path = os.path.join(PROJECT_DIR, "data_summaries", f"{key}-й_ГЕННЫЙ_КЛЮЧ_summary.pdf")
        used_files.append(file_path)
        
        try:
            # Извлекаем текст из PDF-файла
            content = get_pdf_content(file_path)
            gene_text += f"\n--- Описание генного ключа {key} ---\n{content}\n"
        except Exception as e:
            gene_text += f"\n--- Не удалось загрузить описание для генного ключа {key}: {e} ---\n"
    
    # Выводим список используемых файлов (для отладки)
    logger.debug("Используемые файлы для описания генных ключей:")
    for file in used_files:
        logger.debug(file)
    
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
        type_shown (bool): Был ли уже показан тип личности
        
    Returns:
        str: Сгенерированный ответ
    """
    log_debug(logger, f"answer_with_rag вызван с запросом: '{query[:50]}...'")
    log_debug(logger, f"Длина истории диалога: {len(conversation_history)} символов")
    
    # Проверяем, есть ли данные API для печати
    has_holos_data = isinstance(holos_data, dict) and ('api_response' in holos_data or (isinstance(holos_data.get('api_response'), dict)))
    
    # Вывод полных данных API для анализа в отладочный режим
    if has_holos_data and logger.isEnabledFor(10):  # DEBUG = 10
        log_debug(logger, "=== ПОЛНЫЕ ДАННЫЕ ОТ API HOLOS (Отладка) ===")
        if 'api_response' in holos_data:
            log_debug(logger, json.dumps(holos_data['api_response'], indent=4))
        else:
            log_debug(logger, json.dumps(holos_data, indent=4))
        log_debug(logger, "=== КОНЕЦ ОТЛАДОЧНЫХ ДАННЫХ ===")
    
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
    
    # Выводим промпт для отладки
    logger.debug(f"СИСТЕМНЫЙ ПРОМПТ (первые 500 символов): {system_msg[:500]}...")
    logger.debug(f"ПОЛЬЗОВАТЕЛЬСКИЙ ПРОМПТ (первые 500 символов): {user_prompt[:500]}...")

    # Подсчитываем токены для системного промпта и пользовательского промпта
    system_tokens = count_tokens(system_msg)
    user_tokens = count_tokens(user_prompt)
    total_input_tokens = system_tokens + user_tokens

    log_tokens(logger, f"Запрос к LLM: системный промпт {system_tokens} + пользовательский промпт {user_tokens} = {total_input_tokens} токенов")

    # Пробуем отправить запрос, при ошибке меняем ключ
    max_attempts = 3  # Максимальное количество попыток
    current_attempt = 0
    
    while current_attempt < max_attempts:
        try:
            # Устанавливаем текущий ключ
            current_key = key_manager.get_next_key()
            openai.api_key = current_key
            logger.debug(f"Используем ключ #{key_manager.current_index} из {key_manager.total_keys}")
            
            # Отправляем запрос к ChatGPT
            log_api_request(logger, f"Отправка запроса к модели {CHAT_MODEL}, токенов: {total_input_tokens}")
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
            log_tokens(logger, f"Ответ от LLM: {output_tokens} токенов")
            log_tokens(logger, f"Итого: вход {total_input_tokens} / выход {output_tokens} = {total_input_tokens + output_tokens} токенов")
            log_api_response(logger, f"Получен ответ от модели (первые 100 символов): {answer_content[:100]}...")
            
            # Если успешно, возвращаем ответ
            return answer_content
            
        except Exception as e:
            current_attempt += 1
            logger.error(f"Попытка {current_attempt} из {max_attempts}: {str(e)}")
            
            # Пробуем сменить ключ и повторить запрос
            if current_attempt < max_attempts:
                try:
                    # Обрабатываем ошибку и пробуем получить другой ключ
                    openai.api_key = key_manager.handle_error(e)
                    logger.info(f"Переключились на ключ #{key_manager.current_index} из {key_manager.total_keys}")
                except Exception as handle_error:
                    logger.error(f"Не удалось обработать ошибку API: {str(handle_error)}")
            else:
                logger.error("Превышено максимальное количество попыток запроса к API")
                # Возвращаем сообщение об ошибке, если все попытки не удались
                return "Извините, в данный момент сервис недоступен. Пожалуйста, попробуйте позднее."


def summarize_messages(messages: list, max_tokens: int = 500) -> str:
    """
    Суммаризирует набор сообщений.
    
    Args:
        messages (list): Список сообщений для суммаризации
        max_tokens (int): Максимальная длина суммаризации
        
    Returns:
        str: Краткое содержание сообщений
    """
    logger.info(f"Суммаризация {len(messages)} сообщений с моделью {CHAT_MODEL}")
    
    # Формируем диалог для суммаризации
    conversation = ""
    for msg in messages:
        prefix = "Пользователь: " if msg['sender'] == 'user' else "Бот: "
        conversation += f"{prefix}{msg['content']}\n\n"
    
    # Запрос к OpenAI для суммаризации
    logger.debug(f"Отправляем запрос на суммаризацию к модели: {CHAT_MODEL}")
    
    try:
        log_api_request(logger, "Запрос на суммаризацию диалога")
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
        log_api_response(logger, f"Создана суммаризация: {summary[:50]}...")
        return summary
    except Exception as e:
        logger.error(f"Ошибка при суммаризации: {str(e)}")
        return f"[Ошибка суммаризации: {str(e)}]"