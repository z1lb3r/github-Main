"""
Обработчик для раздела "Хьюман дизайн".
Получает данные через API Holos и генерирует ответ с помощью RAG.
Использует систему баланса для оплаты анализа.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from handlers.consultation_mode import get_end_consultation_keyboard
from services.db import (
    get_user_balance, 
    subtract_from_balance, 
    get_user_profile, 
    save_message,
    user_has_initial_analysis,
    mark_initial_analysis_completed
    
)
from services.holos_api import send_request_to_holos
from services.rag_utils import answer_with_rag, count_tokens
from logger import handlers_logger as logger
from logger import log_tokens

from config import (
    HOLOS_DREAM_URL, 
    TOKEN_PRICE, 
    MIN_REQUIRED_BALANCE,
    HD_ANALYSIS_TOKENS
)

router = Router()

router.message(lambda msg: msg.text and msg.text.lower() == "хьюман дизайн")
async def handle_human_design(message: Message, state: FSMContext):
    """
    Обработчик для раздела "Хьюман дизайн".
    Получает данные о пользователе, отправляет запрос к API Holos,
    генерирует ответ с помощью RAG. Списывает средства за анализ.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    user_id = message.from_user.id
    
    # Рассчитываем стоимость анализа Human Design
    hd_cost = HD_ANALYSIS_TOKENS * TOKEN_PRICE
    
    # Проверяем наличие достаточного баланса
    balance = get_user_balance(user_id)
    
    # Добавляем отладочную информацию
    logger.debug(f"Проверка баланса для анализа HD: user_id={user_id}, баланс={balance:.0f} кредитов, требуется={hd_cost:.0f} кредитов")
    
    if balance < hd_cost:
        # Если баланс недостаточен, предлагаем пополнить
        logger.warning(f"Недостаточно средств у пользователя {user_id} для анализа Human Design")
        builder = InlineKeyboardBuilder()
        builder.button(
            text=f"Пополнить баланс",
            callback_data="deposit_balance"
        )
        await message.answer(
            f"⚠️ Недостаточно средств на балансе для анализа Human Design!\n\n"
            f"Стоимость анализа: {hd_cost:.0f} кредитов\n"
            f"Ваш текущий баланс: {balance:.0f} кредитов\n\n"
            "Пожалуйста, пополните баланс для проведения анализа.",
            reply_markup=builder.as_markup()
        )
        return

    # Получаем профиль пользователя
    profile = get_user_profile(user_id)
    if not profile:
        logger.warning(f"Профиль пользователя {user_id} не заполнен")
        await message.answer(
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
        logger.error(f"Ошибка при списании средств для пользователя {user_id}")
        await message.answer(
            "Произошла ошибка при списании средств. Пожалуйста, попробуйте позже."
        )
        return
    
    # Уведомляем пользователя о списании средств
    logger.info(f"Списано {hd_cost:.0f} кредитов за анализ HD для пользователя {user_id}")
    await message.answer(
        f"💸 С вашего баланса списано {hd_cost:.0f} кредитов за анализ Human Design.\n"
        f"Выполняем анализ, пожалуйста, подождите..."
    )

    # Формируем строку даты и времени рождения
    date_str = f"{profile['birth_date']} {profile['birth_time']}"  # формат: ГГГГ-ММ-ДД ЧЧ:ММ
    latitude = profile["latitude"]
    longitude = profile["longitude"]
    altitude = profile["altitude"]

    # Отправляем запрос к API Holos
    logger.info(f"Отправка запроса к API Holos для пользователя {user_id}")
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
    
    # Проверяем, был ли у пользователя уже проведен первичный анализ
    is_initial_analysis = not user_has_initial_analysis(user_id)
    logger.debug(f"Первичный анализ для пользователя {user_id}: {'НЕ проводился (будет выполнен)' if is_initial_analysis else 'УЖЕ проводился (будет приветствие)'}")
    
    # Единый текст консультации независимо от того, первичный это анализ или нет
    expert_prompt = """
            Определи тип личности на основе предоставленных данных API.
            ВАЖНО: Используй следующие поля из структуры API-ответа для определния типа личности:
            - 'type' - для определения типа (manifestor, projector, generator, mangenerator, reflector)
            - 'profile' - для определения профиля (например, 4/1)
            - 'authority' - для определения авторитета (например, splenic, emotional)

            Эти поля находятся в корне объекта data API-ответа.
            НЕ придумывай тип, а используй ТОЛЬКО тот, который указан в поле 'type'.

            После указания типа, объясни 1-2 ключевые особенности, а затем дай конкретные практические советы по улучшению отношений с другими людьми.
    
            После определения типа личности, вставь следующий текст:

            Скажи, какой вопрос ты бы хотел сейчас обсудить? Для тебя сейчас на первом месте отношения семейные, романтические, рабочие или, может быть, дружеские? Или ты хочешь поговорить о личных вопросах?
            
            Я могу помочь, например, в таких областях:
            1. Как наладить общение и избегать недопонимания с близкими или коллегами.
            2. Как мягко устанавливать личные границы, чтобы тебя уважали, но отношения не портились.
            3. Как поддерживать и развивать дружбу или романтические отношения, чтобы они приносили радость.
            4. Помочь тебе понять свое предназначение.
            5. Помочь решить вопросы, связанные с финансами.

            Расскажи, что для тебя актуально — и я дам конкретные рекомендации для твоей ситуации! Просто напиши текстом прямо в чат! Если же ты не можешь определить, то нажми на кнопку "Выбрать тему консультации" и я предложу на выбор наиболее популярные темы для обсуждения.
       """

    # Если это первичный анализ, отмечаем это в БД
    if is_initial_analysis:
        mark_initial_analysis_completed(user_id)
        logger.info(f"Отмечено, что первичный анализ выполнен для пользователя {user_id}")
   
    # Генерируем ответ с помощью RAG - убрали параметр type_shown
    logger.info(f"Генерация ответа с RAG для пользователя {user_id}")
    expert_comment = answer_with_rag(
        expert_prompt,
        holos_data_combined,
        mode="free",
        conversation_history="",
        max_tokens=1200
    )
   
    # Сохраняем ответ бота в базу данных
    save_message(user_id, 'bot', expert_comment)
    logger.info(f"Сохранен ответ бота для пользователя {user_id}")
    
    # Отправляем ответ
    if len(expert_comment) > 4096:
        chunk_size = 4096
        logger.debug(f"Ответ слишком длинный ({len(expert_comment)} символов), разбиваем на части")
        for i in range(0, len(expert_comment), chunk_size):
            await message.answer(expert_comment[i:i+chunk_size])
    else:
        await message.answer(expert_comment)
   
    # Получаем обновленный баланс и сообщаем о возможности задать вопросы
    new_balance = get_user_balance(user_id)
    logger.info(f"Анализ HD завершен для пользователя {user_id}, новый баланс: {new_balance:.0f} кредитов")
    await message.answer(
        f"Анализ Human Design завершен!\n\n"
        f"💰 Ваш текущий баланс: {new_balance:.0f} кредитов \n\n"
        "Теперь вы можете задавать вопросы по теме. "
        "Каждый вопрос и ответ будут тарифицироваться согласно количеству используемых токенов.",
        reply_markup=get_end_consultation_keyboard()
    )
   
    # Сохраняем начальную историю диалога и данные API в состоянии
    await state.update_data(
        conversation_history=f"Бот: {expert_comment}\n",
        holos_response=holos_data_combined,
        in_consultation=True  # Добавляем флаг активного режима консультации
    )