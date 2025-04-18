"""
Основной файл для запуска Telegram бота.
Инициализирует бота, регистрирует обработчики и запускает поллинг.
"""
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import CONFIG_TELEGRAM_BOT_TOKEN
from handlers.command_handlers import router as command_handlers_router
from handlers.onboarding import router as onboarding_router
from handlers.main_menu import router as main_menu_router
from handlers.section_choice import router as section_choice_router
from handlers.human_design import router as human_design_router
from handlers.payment import router as payment_router
from handlers.conversation import router as conversation_router
from handlers.change_data import router as change_data_router
from handlers.referral import router as referral_router
from handlers.consultation_mode import router as consultation_mode_router
from handlers.topics import router as topics_router
from handlers.compatibility import router as compatibility_router
from services.db import init_db
import threading
from db_api import app as db_api_app

def main():
    """
    Основная функция запуска бота.
    Инициализирует бота, хранилище состояний, диспетчер и регистрирует обработчики.
    """
    # Создаем экземпляр бота с токеном из конфига
    bot = Bot(token=CONFIG_TELEGRAM_BOT_TOKEN)
    
    # Создаем хранилище состояний в памяти
    storage = MemoryStorage()
    
    # Создаем диспетчер с хранилищем состояний
    dp = Dispatcher(storage=storage)

    # Инициализируем базу данных
    init_db()
    
    # Запускаем API для базы данных в отдельном потоке
    db_api_thread = threading.Thread(target=lambda: db_api_app.run(host='0.0.0.0', port=5001, debug=False))
    db_api_thread.daemon = True
    db_api_thread.start()
    print("Database API started on port 5001")

    # Регистрируем маршрутизаторы (обработчики сообщений)
    # Порядок важен: более специфичные обработчики должны идти раньше общих
    dp.include_router(command_handlers_router)    # Обработчики команд
    dp.include_router(onboarding_router)          # Обработчики онбординга
    dp.include_router(compatibility_router)       # Обработчики проверки совместимости
    dp.include_router(main_menu_router)           # Обработчики главного меню
    dp.include_router(change_data_router)         # Обработчики изменения данных
    dp.include_router(referral_router)            # Обработчики реферальной системы
    dp.include_router(consultation_mode_router)   # Обработчики режима консультации
    dp.include_router(topics_router)              # Обработчики тематических консультаций
    dp.include_router(section_choice_router)      # Обработчики выбора разделов
    dp.include_router(human_design_router)        # Обработчики для Human Design
    dp.include_router(payment_router)             # Обработчики для платежей
    dp.include_router(conversation_router)        # Общий обработчик сообщений

    # Настраиваем параметры для отправки больших медиафайлов
    bot_settings = {
        "parse_mode": None,  # Используем None вместо HTML для избежания ошибок форматирования
        "disable_web_page_preview": True
    }

    # Запускаем поллинг сообщений
    dp.run_polling(bot, **bot_settings)

if __name__ == "__main__":
    main()