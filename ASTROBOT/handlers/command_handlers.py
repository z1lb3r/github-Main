"""
Обработчики команд Telegram-бота.
Обрабатывает команды /start, /subscribe, /unsubscribe, /status, /payment, /menu.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
# Правильный импорт из onboarding.py
from handlers.onboarding import start_onboarding
from handlers.payment import get_payment_keyboard
from handlers.change_data import get_updated_main_menu_keyboard

from .keyboards import main_menu_kb
from services.db import (
    add_user_if_not_exists,
    activate_subscription,
    deactivate_subscription,
    user_has_active_subscription,
    get_user_profile,
    add_referral
)

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start.
    Регистрирует пользователя и предлагает пройти онбординг, если профиль не заполнен.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    # Добавляем отладочный вывод
    print(f"cmd_start для пользователя {user_id} ({username})")
    
    # Получаем профиль пользователя
    profile = get_user_profile(user_id)
    
    # Еще отладочный вывод
    print(f"Полученный профиль: {profile}")
    
    # Проверяем, содержит ли команда start параметры
    ref_params = message.text.split(' ')
    if len(ref_params) > 1:
        param = ref_params[1]
        
        # Проверяем, является ли это приглашением для проверки совместимости
        if param.startswith('comp_'):
            invite_code = param[5:]  # Убираем префикс comp_
            print(f"Пользователь {user_id} пришел по приглашению для проверки совместимости: {invite_code}")
            
            # Если профиль заполнен, обрабатываем приглашение
            if get_user_profile(user_id):
                from handlers.compatibility import process_compatibility_invitation
                await process_compatibility_invitation(message, invite_code)
                return
            # Иначе сохраняем код приглашения для обработки после регистрации
            else:
                await state.update_data(start_invite_code=invite_code)
        
        # Если это не приглашение для совместимости, проверяем реферальную ссылку
        try:
            ref_user_id = int(param)
            # Добавляем реферальную связь, если пользователи разные
            if ref_user_id != user_id:
                add_referral(user_id, ref_user_id)
                print(f"Пользователь {user_id} пришел по реферальной ссылке от {ref_user_id}")
        except ValueError:
            pass
    
    # Добавляем пользователя в БД, если его там еще нет
    add_user_if_not_exists(user_id, username)
    
    # Получаем профиль пользователя
    profile = get_user_profile(user_id)
    
    if not profile:
        # Если профиль не заполнен, запускаем анкетирование
        await message.answer("Добро пожаловать! Для начала работы необходимо заполнить анкету.")
        await start_onboarding(message, state)
    else:
        # Если профиль заполнен, показываем главное меню с обновленной клавиатурой
        await message.answer(
        f"👋 Привет и добро пожаловать! \n\n"
        f"🧠 Мы предлагаем уникальный продукт - консультанта по отношениям между людьми на основе искусственного интеллекта обученного профессиональными психологами.\n\n"
        f"✨ Наш консультант поможет:\n"
        f"• Узнать свою совместимость со второй половинкой\n"
        f"• Подготовиться к важным переговорам\n"
        f"• Понять, как донести нужную мысль до ребенка\n"
        f"• И многое другое!\n\n"
        f"🔍 Наша команда состоящая из специалистов по психологии и Human Design создали продукт, нацеленный на решение задач в области отношений между людьми и самопознания\n\n"
        f"📚 Наш ИИ пользуется специально отобранными источниками данных для формирования ответов, которые регулярно обновляются.\n\n"
        f"🚀 Быстрый старт: \n"
        f"Для теста продукта вы можете сделать один бесплатный разбор с любым человеком отправив ему ссылку приглашение\n\n"
        f"Для более подробных консультаций вам потребуется пополнить баланс, который будет расходоваться по мере проведения консультации \n"
        f"1️⃣ Для проведения полноценной консультации с возможность задать любые дополнительные вопросы рекомендуем пополнить баланс на сумму от 300 рублей\n"
        f"2️⃣ Далее выберите раздел из меню \"✨ Начать консультацию\"\n"
        f"3️⃣ Если захотите продолжить уже начатую консультацию, выберите \"🔄 Продолжить консультацию\"\n\n"
        f"⬇️ Выберите раздел в меню, чтобы начать:",
        reply_markup=get_updated_main_menu_keyboard()
)

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """
    Обработчик команды /menu.
    Показывает главное меню бота.
    
    Args:
        message (Message): Сообщение Telegram
    """
    await message.answer(
        "Главное меню бота:",
        reply_markup=get_updated_main_menu_keyboard()
    )

@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    """
    Обработчик команды /subscribe.
    Предлагает пользователю оплатить подписку, если она еще не активирована.
    
    Args:
        message (Message): Сообщение Telegram
    """
    # Проверяем, есть ли уже активная подписка
    if user_has_active_subscription(message.from_user.id):
        await message.answer("У вас уже есть активный баланс на аккаунте.")
        return
    
    # Предлагаем оплатить подписку через CrystalPay
    await message.answer(
        "Для активации баланса, пожалуйста, пополните его. "
        "Вы можете сделать это через команду /payment.",
        reply_markup=get_payment_keyboard()
    )

@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message):
    """
    Обработчик команды /unsubscribe.
    Деактивирует подписку пользователя.
    
    Args:
        message (Message): Сообщение Telegram
    """
    deactivate_subscription(message.from_user.id)
    await message.answer("Ваш баланс обнулен. Если захотите продолжить, вы можете пополнить его через /payment.")

@router.message(Command("status"))
async def cmd_status(message: Message):
    """
    Обработчик команды /status.
    Показывает статус баланса пользователя.
    
    Args:
        message (Message): Сообщение Telegram
    """
    from services.db import get_user_balance
    balance = get_user_balance(message.from_user.id)
    await message.answer(f"Ваш текущий баланс: ${balance:.2f}.")

@router.message(Command("payment"))
async def cmd_payment(message: Message):
    """
    Обработчик команды /payment.
    Показывает информацию о пополнении баланса.
    
    Args:
        message (Message): Сообщение Telegram
    """
    from handlers.main_menu import show_balance
    await show_balance(message)

@router.message(Command("pay"))
async def cmd_pay(message: Message):
    """
    Альтернативная команда для /payment.
    """
    from handlers.main_menu import show_balance
    await show_balance(message)

@router.message(Command("about"))
async def cmd_about(message: Message):
    """
    Обработчик команды /about.
    Показывает информацию о боте.
    
    Args:
        message (Message): Сообщение Telegram
    """
    from handlers.main_menu import show_about_us
    await show_about_us(message)

@router.message(Command("terms"))
async def cmd_terms(message: Message):
    """
    Обработчик команды /terms.
    Показывает пользовательское соглашение.
    
    Args:
        message (Message): Сообщение Telegram
    """
    from handlers.main_menu import show_terms
    await show_terms(message)

@router.message(Command("referral"))
async def cmd_referral(message: Message):
    """
    Обработчик команды /referral.
    Показывает информацию о реферальной программе.
    
    Args:
        message (Message): Сообщение Telegram
    """
    from handlers.referral import show_referral_program_enhanced
    await show_referral_program_enhanced(message)

@router.message(Command("contacts"))
async def cmd_contacts(message: Message):
    """
    Обработчик команды /contacts.
    Показывает контактную информацию.
    
    Args:
        message (Message): Сообщение Telegram
    """
    from handlers.main_menu import show_contacts
    await show_contacts(message)

@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработчик команды /help.
    Показывает список доступных команд.
    
    Args:
        message (Message): Сообщение Telegram
    """
    help_text = (
        "📋 Список доступных команд:\n\n"
        "/start - Начать работу с ботом\n"
        "/menu - Показать главное меню\n"
        "/payment - Пополнить баланс\n"
        "/status - Проверить баланс\n"
        "/about - О нас\n"
        "/terms - Пользовательское соглашение\n"
        "/referral - Реферальная программа\n"
        "/changedata - Изменить мои данные\n"
        "/contacts - Контактная информация\n"
        "/help - Показать эту справку"
    )
    await message.answer(help_text, reply_markup=get_updated_main_menu_keyboard())

@router.message(Command("changedata"))
async def cmd_change_data(message: Message, state: FSMContext):
    """
    Обработчик команды /changedata.
    Запускает процесс изменения данных пользователя.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    from handlers.change_data import change_user_data
    await change_user_data(message, state)