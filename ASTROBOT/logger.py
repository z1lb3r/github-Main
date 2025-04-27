"""
Централизованная настройка логирования для телеграм-бота.
Предоставляет логгеры для всех компонентов приложения.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime

# Создаем директорию для логов, если её нет
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Настройка форматирования
# Формат для файлов (с датой)
FILE_FORMAT = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Формат для консоли (без даты, более компактный)
CONSOLE_FORMAT = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

# Настройка обработчиков
def setup_file_handler(log_file, level=logging.INFO):
    """Создает и настраивает обработчик логов для файла с ротацией."""
    file_path = os.path.join(LOGS_DIR, log_file)
    file_handler = RotatingFileHandler(
        file_path, 
        maxBytes=10*1024*1024,  # 10 МБ
        backupCount=5            # 5 резервных копий
    )
    file_handler.setFormatter(FILE_FORMAT)
    file_handler.setLevel(level)
    return file_handler

def setup_console_handler(level=logging.INFO):
    """Создает и настраивает обработчик для вывода в консоль."""
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CONSOLE_FORMAT)
    console_handler.setLevel(level)
    return console_handler

# Настройка основного логгера
def get_logger(name, log_file=None, console_level=logging.INFO, file_level=logging.DEBUG):
    """
    Создает и возвращает настроенный логгер.
    
    Args:
        name (str): Имя логгера
        log_file (str, optional): Имя файла для логирования. Если None, логи пишутся только в консоль.
        console_level (int): Уровень логирования для консоли
        file_level (int): Уровень логирования для файла
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Устанавливаем базовый уровень логгера
    
    # Очищаем обработчики, если они уже есть
    if logger.handlers:
        logger.handlers.clear()
    
    # Добавляем обработчик консоли
    logger.addHandler(setup_console_handler(console_level))
    
    # Если указано имя файла, добавляем файловый обработчик
    if log_file:
        logger.addHandler(setup_file_handler(log_file, file_level))
    
    # Запрещаем передачу логов родительским логгерам
    logger.propagate = False
    
    return logger

# Создаем основные логгеры приложения
# Главный логгер
main_logger = get_logger('bot', 'bot.log')

# Логгер для базы данных
db_logger = get_logger('db', 'database.log')

# Логгер для API запросов
api_logger = get_logger('api', 'api.log')

# Логгер для обработчиков сообщений
handlers_logger = get_logger('handlers', 'handlers.log')

# Логгер для сервисных функций
services_logger = get_logger('services', 'services.log')

# Логгер для отслеживания токенов и оплаты
tokens_logger = get_logger('tokens', 'tokens.log')

# Функции-хелперы для специальных типов логов
def log_api_request(logger, message):
    """Логирует API запрос."""
    logger.info(f"[API REQUEST] {message}")

def log_api_response(logger, message):
    """Логирует ответ от API."""
    logger.info(f"[API RESPONSE] {message}")

def log_api_error(logger, message):
    """Логирует ошибку API."""
    logger.error(f"[API ERROR] {message}")

def log_tokens(logger, message):
    """Логирует информацию о токенах."""
    logger.info(f"[TOKENS] {message}")

def log_payment(logger, message):
    """Логирует информацию о платежах."""
    logger.info(f"[PAYMENT] {message}")

def log_debug(logger, message):
    """Логирует отладочную информацию."""
    logger.debug(f"[DEBUG] {message}")

def setup_module_logger(module_name):
    """
    Создает и возвращает логгер для конкретного модуля с унифицированной настройкой.
    
    Args:
        module_name (str): Имя модуля
        
    Returns:
        logging.Logger: Настроенный логгер для модуля
    """
    # Создаем имя для логера на основе имени модуля
    logger_name = f"bot.{module_name}"
    
    # Создаем имя файла на основе имени модуля
    log_file = f"{module_name}.log"
    
    # Возвращаем настроенный логгер
    return get_logger(logger_name, log_file)