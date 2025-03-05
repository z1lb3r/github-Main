"""
Обработчики для главного меню бота и всех его разделов.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .keyboards import (
    main_menu_kb, 
    get_back_to_menu_keyboard,
    get_consultation_confirmation_keyboard
)
from services.db import get_user_balance, get_transaction_history, get_user_profile, subtract_from_balance
from config import MIN_REQUIRED_BALANCE
from handlers.change_data import get_updated_main_menu_keyboard
from handlers.consultation_mode import (
    start_consultation_mode, 
    is_in_consultation,
    get_end_consultation_keyboard
)
from handlers.referral import show_referral_program_enhanced, show_ref_stats_enhanced

router = Router()

# Обработчик команды /menu
@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """
    Показывает главное меню бота.
    """
    await message.answer("Выберите раздел:", reply_markup=get_updated_main_menu_keyboard())

# Обработчик кнопки "Начать консультацию"
@router.message(F.text == "✨ Начать консультацию")
async def start_consultation(message: Message, state: FSMContext):
    """
    Обработчик кнопки "Начать консультацию".
    Проверяет данные пользователя и баланс, предлагает начать консультацию.
    """
    user_id = message.from_user.id
    
    # Проверяем, находится ли пользователь уже в режиме консультации
    in_consultation = await is_in_consultation(state)
    print(f"Начало консультации: user_id={user_id}, уже в консультации={in_consultation}")
    
    if in_consultation:
        await message.answer(
            "Вы уже находитесь в режиме консультации. Вы можете продолжать задавать вопросы "
            "или завершить консультацию, нажав на кнопку ниже.",
            reply_markup=get_end_consultation_keyboard()
        )
        return
    
    # Проверяем профиль пользователя
    profile = get_user_profile(user_id)
    if not profile:
        await message.answer(
            "Для начала консультации необходимо заполнить ваши данные. "
            "Пожалуйста, введите /start для заполнения профиля.",
            reply_markup=get_updated_main_menu_keyboard()
        )
        return
    
    # Проверяем баланс пользователя
    balance = get_user_balance(user_id)
    print(f"Проверка баланса для консультации: user_id={user_id}, баланс={balance:.0f} баллов, минимум={MIN_REQUIRED_BALANCE:.0f} баллов")
    
    if balance < MIN_REQUIRED_BALANCE:
        await message.answer(
            f"⚠️ Недостаточно средств для начала консультации.\n\n"
            f"Ваш текущий баланс: {balance:.0f} баллов\n"
            f"Минимальный баланс для консультации: {MIN_REQUIRED_BALANCE:.0f} баллов\n\n"
            f"Пожалуйста, пополните баланс в разделе 'Баланс'.",
            reply_markup=get_updated_main_menu_keyboard()
        )
        return
    
    # Предлагаем начать консультацию
    await message.answer(
        "🔮 Вы готовы начать консультацию по Human Design?\n\n"
        "Консультация включает анализ вашей энергетической карты на основе "
        "даты, времени и места рождения, а также ответы на ваши вопросы.\n\n"
        f"Стоимость анализа: {MIN_REQUIRED_BALANCE:.0f} баллов\n"
        f"Ваш текущий баланс: {balance:.0f} баллов",
        reply_markup=get_consultation_confirmation_keyboard()
    )

# Обработчик кнопки "Баланс"
@router.message(F.text == "💰 Баланс")
async def show_balance(message: Message):
    """
    Обработчик кнопки "Баланс".
    Показывает текущий баланс и опции для работы с ним.
    """
    balance = get_user_balance(message.from_user.id)
    print(f"Показ баланса: user_id={message.from_user.id}, баланс={balance:.0f} баллов")
    
    # Заменяем get_balance_keyboard на новую функцию без кнопки вывода средств
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💵 Пополнить баланс",
        callback_data="deposit_balance"
    )
    builder.button(
        text="📊 История транзакций",
        callback_data="transaction_history"
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main_menu")
    )
    
    await message.answer(
        f"💰 Ваш текущий баланс: {balance:.0f} баллов\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup()
    )

# Обработчик кнопки "Пополнить"
@router.callback_query(F.data == "deposit_balance")
async def deposit_balance(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "Пополнить".
    Запускает процесс пополнения через CrystalPay.
    """
    await callback.answer()
    
    # Используем функциональность уже имеющегося обработчика пополнения
    from handlers.payment import process_deposit_start
    await process_deposit_start(callback, state)

# Обработчик кнопки "Пользовательское соглашение"
@router.message(F.text == "📋 Пользовательское соглашение")
async def show_terms(message: Message):
    """
    Обработчик кнопки "Пользовательское соглашение".
    Показывает текст пользовательского соглашения.
    """
    terms_text = """
# Пользовательское соглашение

## 1. Общие положения

Настоящее Пользовательское соглашение (далее – «Соглашение») регулирует отношения между владельцем Telegram-бота "@cz_astrobot" (далее – «Сервис») и физическим лицом (далее – «Пользователь»), использующим услуги Сервиса.

Используя Сервис, Пользователь подтверждает, что полностью принимает условия настоящего Соглашения.

## 2. Предмет соглашения

Сервис предоставляет Пользователю возможность получать консультации в области Human Design и астрологии посредством обмена сообщениями через интерфейс Telegram-бота.

## 3. Порядок использования Сервиса

3.1. Для использования Сервиса Пользователь должен предоставить свои персональные данные, включая имя, дату и точное время рождения, а также место рождения.

3.2. Оплата услуг Сервиса осуществляется через платежную систему CrystalPay по модели "оплата за использование" (pay-per-use).

3.3. Стоимость услуг рассчитывается исходя из количества обработанных токенов и устанавливается в баллах (1 балл = 1 рубль).

## 4. Права и обязанности Сторон

4.1. Пользователь обязуется:
- Предоставлять достоверную информацию о себе
- Не использовать Сервис для незаконных целей
- Своевременно оплачивать услуги Сервиса

4.2. Сервис обязуется:
- Обеспечивать конфиденциальность персональных данных Пользователя
- Предоставлять качественные консультации в области Human Design
- Обеспечивать доступность Сервиса с учетом технических возможностей

## 5. Ограничение ответственности

5.1. Консультации, предоставляемые Сервисом, носят информационный характер и не являются медицинскими, психологическими или юридическими рекомендациями.

5.2. Сервис не несет ответственности за решения, принятые Пользователем на основе полученных консультаций.

5.3. Сервис не гарантирует непрерывную работу и может временно приостанавливать доступ для технического обслуживания.

## 6. Персональные данные

6.1. Пользователь соглашается на обработку своих персональных данных для целей оказания услуг.

6.2. Сервис обязуется не передавать персональные данные Пользователя третьим лицам, за исключением случаев, предусмотренных законодательством.

## 7. Порядок оплаты

7.1. Оплата услуг производится через платежную систему CrystalPay.

7.2. Пользователь самостоятельно оплачивает услуги связи и доступа в интернет.

## 8. Срок действия и изменение соглашения

8.1. Соглашение действует бессрочно до момента его расторжения.

8.2. Сервис имеет право в одностороннем порядке изменять условия Соглашения. Новая редакция Соглашения вступает в силу с момента ее публикации.

## 9. Заключительные положения

9.1. Все споры по настоящему Соглашению разрешаются путем переговоров.

9.2. Во всем остальном, что не урегулировано настоящим Соглашением, стороны руководствуются действующим законодательством.
"""
    
    # Разбиваем на части, если текст слишком длинный
    max_length = 4000
    if len(terms_text) <= max_length:
        await message.answer(
            terms_text,
            reply_markup=get_back_to_menu_keyboard()
        )
    else:
        parts = [terms_text[i:i+max_length] for i in range(0, len(terms_text), max_length)]
        for i, part in enumerate(parts):
            if i == len(parts) - 1:  # Если это последняя часть
                await message.answer(
                    part,
                    reply_markup=get_back_to_menu_keyboard()
                )
            else:
                await message.answer(part)

# Обработчик кнопки "О нас"
@router.message(F.text == "ℹ️ О нас")
async def show_about_us(message: Message):
    """
    Обработчик кнопки "О нас".
    Показывает информацию о продукте.
    """
    about_text = """
# Астро-консультант: Персональный гид в мире Human Design

Представляем вам инновационного Telegram-бота, совмещающего древнюю мудрость астрологии и современные технологии искусственного интеллекта для создания персонализированных консультаций по системе Human Design.

Наш бот – это персональный консультант, который помогает раскрыть ваш внутренний потенциал и найти свой уникальный путь к гармонии и самореализации. Основываясь на точных данных о дате, времени и месте вашего рождения, он создает детальный анализ вашей энергетической карты, выявляя ваши природные таланты, оптимальные стратегии принятия решений и потенциальные области для личностного роста.

Система Human Design объединяет древние знания И-Цзин, Каббалы, астрологии и генетики в единую систему самопознания. Наш бот делает эти сложные знания доступными и применимыми в повседневной жизни, помогая вам:

- Понять свой тип энергии и стратегию взаимодействия с миром
- Выявить ваши врожденные таланты и способы их реализации
- Определить оптимальные пути принятия решений в соответствии с вашим внутренним авторитетом
- Разрешить внутренние конфликты и избавиться от чувства вины за непохожесть на других
- Выстроить гармоничные отношения с окружающими, основанные на понимании различий

Благодаря передовым технологиям искусственного интеллекта, наш бот предоставляет не только общую информацию, но и глубокий анализ конкретно вашей ситуации, отвечая на индивидуальные вопросы об отношениях, карьере, здоровье и личностном развитии.

Мы используем гибкую систему оплаты, основанную на фактическом использовании, что делает консультации доступными для широкого круга пользователей. Вы платите только за те вопросы, которые задаете, без обязательных подписок и скрытых платежей.
"""
    
    await message.answer(
        about_text,
        reply_markup=get_back_to_menu_keyboard()
    )

# Обработчик кнопки "Реферальная программа"
@router.message(F.text == "👥 Реферальная программа")
async def show_referral_program(message: Message):
    """
    Обработчик кнопки "Реферальная программа".
    Показывает информацию о реферальной программе.
    """
    await show_referral_program_enhanced(message)

# Обработчик кнопки "Изменить мои данные"
@router.message(F.text == "👤 Изменить мои данные")
async def handle_change_data(message: Message, state: FSMContext):
    """
    Обработчик кнопки "Изменить мои данные".
    """
    from handlers.change_data import change_user_data
    await change_user_data(message, state)

# Обработчик копирования реферальной ссылки
@router.callback_query(F.data == "copy_ref_link")
async def copy_ref_link(callback: CallbackQuery):
    """
    Обработчик копирования реферальной ссылки.
    """
    # Явно указываем правильное имя бота
    bot_username = "cz_astrobot_bot"  # Правильное имя бота с подчеркиванием
    
    user_id = callback.from_user.id
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    
    await callback.answer("Ссылка скопирована!")
    await callback.message.answer(
        f"Ваша реферальная ссылка:\n{ref_link}\n\n"
        "Ссылка скопирована в буфер обмена."
    )

# Обработчик просмотра статистики приглашений
@router.callback_query(F.data == "ref_stats")
async def show_ref_stats(callback: CallbackQuery):
    """
    Обработчик просмотра статистики приглашений.
    """
    await show_ref_stats_enhanced(callback)

# Обработчик возврата в главное меню
@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """
    Обработчик возврата в главное меню.
    """
    await callback.answer()
    await callback.message.answer(
        "Вы вернулись в главное меню.",
        reply_markup=get_updated_main_menu_keyboard()
    )

# Обработчик подтверждения начала консультации
@router.callback_query(F.data == "start_consultation")
async def confirm_consultation(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик подтверждения начала консультации.
    Перенаправляет на обработчик Human Design и включает режим консультации.
    """
    await callback.answer()
    
    # Включаем режим консультации
    user_id = callback.from_user.id
    await start_consultation_mode(user_id, state)
    
    # Получаем данные пользователя и настройки анализа HD
    from handlers.human_design import HD_ANALYSIS_TOKENS, TOKEN_PRICE, HOLOS_DREAM_URL
    from services.db import get_user_balance, subtract_from_balance, get_user_profile
    from services.holos_api import send_request_to_holos
    from services.rag_utils import answer_with_rag
    
    # Рассчитываем стоимость анализа Human Design
    hd_cost = HD_ANALYSIS_TOKENS * TOKEN_PRICE
    
    # Проверяем баланс пользователя еще раз
    balance = get_user_balance(user_id)
    print(f"Проверка баланса для анализа HD в confirm_consultation: user_id={user_id}, баланс={balance:.0f} баллов, требуется={hd_cost:.0f} баллов")
    
    if balance < hd_cost:
        await callback.message.answer(
            f"⚠️ Недостаточно средств на балансе для анализа Human Design!\n\n"
            f"Стоимость анализа: {hd_cost:.0f} баллов\n"
            f"Ваш текущий баланс: {balance:.0f} баллов\n\n"
            "Пожалуйста, пополните баланс для проведения анализа."
        )
        return

    # Получаем профиль пользователя
    profile = get_user_profile(user_id)
    if not profile:
        await callback.message.answer(
            "Ваш профиль не заполнен. Для заполнения данных выберите 'Изменить мои данные' или введите /start."
        )
        return

    # Списываем средства за анализ Human Design
    success = subtract_from_balance(
        user_id, 
        hd_cost, 
        f"Анализ Human Design ({HD_ANALYSIS_TOKENS} токенов)"
    )
    
    if not success:
        await callback.message.answer(
            "Произошла ошибка при списании средств. Пожалуйста, попробуйте позже."
        )
        return
    
    # Уведомляем пользователя о списании средств
    await callback.message.answer(
        f"💸 С вашего баланса списано {hd_cost:.0f} баллов за анализ Human Design.\n"
        f"Выполняем анализ, пожалуйста, подождите..."
    )

    # Формируем строку даты и времени рождения
    date_str = f"{profile['birth_date']} {profile['birth_time']}"  # формат: ГГГГ-ММ-ДД ЧЧ:ММ
    latitude = profile["latitude"]
    longitude = profile["longitude"]
    altitude = profile["altitude"]

    # Отправляем запрос к API Holos
    response_data = await send_request_to_holos(
        holos_url=HOLOS_DREAM_URL,
        date_str=date_str,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude
    )
    
    # Собираем данные пользователя в виде строки
    user_profile_info = (
        f"Дата рождения: {profile['birth_date']}\n"
        f"Время рождения: {profile['birth_time']}\n"
        f"Место рождения (координаты): {latitude}, {longitude}, {altitude}\n"
        f"Данные API: {response_data}"
    )
    
    holos_data_combined = {
        "user_profile": user_profile_info,
        "api_response": response_data
    }
    
    # Генерируем ответ с помощью RAG
    expert_comment = answer_with_rag(
        "Проанализируй данные и дай описание и практические рекомендации по 4 аспектам: "
        "отношения/любовь, финансы, здоровье, источники счастья.",
        holos_data_combined,
        mode="4_aspects",
        conversation_history="",
        max_tokens=1200
    )
    
    # Отправляем ответ
    if len(expert_comment) > 4096:
        chunk_size = 4096
        for i in range(0, len(expert_comment), chunk_size):
            await callback.message.answer(expert_comment[i:i+chunk_size])
    else:
        await callback.message.answer(expert_comment)
    
    # Получаем обновленный баланс и сохраняем данные в состоянии
    new_balance = get_user_balance(user_id)
    await state.update_data(
        conversation_history=f"Бот: {expert_comment}\n",
        holos_response=holos_data_combined,
        in_consultation=True
    )
    
    # Сообщаем о возможности задавать вопросы и показываем кнопку завершения консультации
    await callback.message.answer(
        f"Анализ Human Design завершен!\n\n"
        f"💰 Ваш текущий баланс: {new_balance:.0f} баллов\n\n"
        "Теперь вы можете задавать вопросы по теме. "
        "Каждый вопрос и ответ будут тарифицироваться согласно количеству используемых токенов. "
        "Когда закончите, нажмите 'Завершить консультацию'.", 
        reply_markup=get_end_consultation_keyboard()
    )