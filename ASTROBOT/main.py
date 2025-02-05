from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import CONFIG_TELEGRAM_BOT_TOKEN
from handlers.command_handlers import router as command_handlers_router
from handlers.onboarding import router as onboarding_router
from handlers.section_choice import router as section_choice_router
from handlers.human_design import router as human_design_router
from handlers.conversation import router as conversation_router

from services.db import init_db

def main():
    bot = Bot(token=CONFIG_TELEGRAM_BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    init_db()  # Инициализируем БД

    # Включаем роутеры в следующем порядке:
    dp.include_router(command_handlers_router)
    dp.include_router(onboarding_router)      # onboarding раньше, чтобы его FSM-обработчики ловили сообщения
    dp.include_router(section_choice_router)
    dp.include_router(human_design_router)
    dp.include_router(conversation_router)      # общий обработчик в самом конце

    dp.run_polling(bot)

if __name__ == "__main__":
    main()
