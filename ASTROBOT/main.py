"""
Основной файл для запуска Telegram бота.
Инициализирует бота, регистрирует обработчики и запускает поллинг.
"""

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import CONFIG_TELEGRAM_BOT_TOKEN
from handlers.command_handlers import router as command_handlers_router
from handlers.onboarding import router as onboarding_router
from handlers.section_choice import router as section_choice_router
from handlers.human_design import router as human_design_router
from handlers.conversation import router as conversation_router
from handlers.payment import router as payment_router

from services.db import init_db

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

    # Регистрируем маршрутизаторы (обработчики сообщений)
    # Порядок важен: более специфичные обработчики должны идти раньше общих
    dp.include_router(command_handlers_router)    # Обработчики команд
    dp.include_router(onboarding_router)          # Обработчики онбординга
    dp.include_router(section_choice_router)      # Обработчики выбора разделов
    dp.include_router(human_design_router)        # Обработчики для Human Design
    dp.include_router(payment_router)             # Маршрутизатор для платежей
    dp.include_router(conversation_router)        # Общий обработчик сообщений
    

    # Запускаем поллинг сообщений
    dp.run_polling(bot)

if __name__ == "__main__":
    main()