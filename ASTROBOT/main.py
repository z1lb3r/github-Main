from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import CONFIG_TELEGRAM_BOT_TOKEN
from handlers.command_handlers import router as command_handlers_router
from handlers.section_choice import router as section_choice_router
from handlers.calculations import router as calculations_router
# Если нужен свободный диалог: from handlers.conversation import router as conversation_router

from services.db import init_db

def main():
    bot = Bot(token=CONFIG_TELEGRAM_BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    init_db()  # Создаём таблицу users, если её нет

    dp.include_router(command_handlers_router)
    dp.include_router(section_choice_router)
    dp.include_router(calculations_router)
    # dp.include_router(conversation_router)  # если есть свободный диалог

    dp.run_polling(bot)

if __name__ == "__main__":
    main()