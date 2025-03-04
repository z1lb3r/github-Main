"""
Обработчик для раздела "Хьюман дизайн".
Получает данные через API Holos и генерирует ответ с помощью RAG.
Использует систему баланса для оплаты анализа.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.db import get_user_balance, subtract_from_balance, get_user_profile
from services.holos_api import send_request_to_holos
from services.rag_utils import answer_with_rag, count_tokens
from config import (
    HOLOS_DREAM_URL, 
    TOKEN_PRICE, 
    DEPOSIT_AMOUNT_USD, 
    DISPLAY_CURRENCY,
    HD_ANALYSIS_TOKENS
)

router = Router()

@router.message(lambda msg: msg.text and msg.text.lower() == "хьюман дизайн")
async def handle_human_design(message: Message, state: FSMContext):
    """
    Обработчик для раздела "Хьюман дизайн".
    Получает данные о пользователе, отправляет запрос к API Holos,
    генерирует ответ с помощью RAG. Списывает средства за анализ.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    # Рассчитываем стоимость анализа Human Design
    hd_cost = HD_ANALYSIS_TOKENS * TOKEN_PRICE
    
    # Проверяем наличие достаточного баланса
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    
    # Добавляем отладочную информацию
    print(f"Проверка баланса для анализа HD: user_id={user_id}, баланс=${balance}, требуется=${hd_cost}")
    
    if balance < hd_cost:
        # Если баланс недостаточен, предлагаем пополнить
        builder = InlineKeyboardBuilder()
        builder.button(
            text=f"Пополнить баланс (${DEPOSIT_AMOUNT_USD:.2f})",
            callback_data="deposit_balance"
        )
        await message.answer(
            f"⚠️ Недостаточно средств на балансе для анализа Human Design!\n\n"
            f"Стоимость анализа: ${hd_cost:.6f}\n"
            f"Ваш текущий баланс: ${balance:.6f}\n\n"
            "Пожалуйста, пополните баланс для проведения анализа.",
            reply_markup=builder.as_markup()
        )
        return

    # Получаем профиль пользователя
    profile = get_user_profile(user_id)
    if not profile:
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
        await message.answer(
            "Произошла ошибка при списании средств. Пожалуйста, попробуйте позже."
        )
        return
    
    # Уведомляем пользователя о списании средств
    await message.answer(
        f"💸 С вашего баланса списано ${hd_cost:.6f} за анализ Human Design.\n"
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
            await message.answer(expert_comment[i:i+chunk_size])
    else:
        await message.answer(expert_comment)
    
    # Получаем обновленный баланс и сообщаем о возможности задать вопросы
    new_balance = get_user_balance(user_id)
    await message.answer(
        f"Анализ Human Design завершен!\n\n"
        f"💰 Ваш текущий баланс: ${new_balance:.6f}\n\n"
        "Теперь вы можете задавать вопросы по теме. "
        "Каждый вопрос и ответ будут тарифицироваться согласно количеству используемых токенов."
    )
    
    # Сохраняем начальную историю диалога и данные API в состоянии
    await state.update_data(
        conversation_history=f"Бот: {expert_comment}\n",
        holos_response=holos_data_combined,
        in_consultation=True  # Добавляем флаг активного режима консультации
    )