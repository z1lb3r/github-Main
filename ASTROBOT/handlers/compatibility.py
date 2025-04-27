"""
Обработчики для проверки совместимости между пользователями.
Позволяет создавать приглашения и анализировать совместимость типов.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from services.db import get_user_profile, check_compatibility_invitation, create_compatibility_invitation, accept_compatibility_invitation, get_user_compatibility_invites, count_user_invites
from services.rag_utils import answer_with_rag
from config import BOT_USERNAME
from logger import handlers_logger as logger

router = Router()

# Определяем состояния для FSM
class CompatibilityStates(StatesGroup):
    waiting_for_compatibility_type = State()

# Обработчик кнопки "Бесплатно проверить совместимость"
@router.message(F.text == "⭐️🔄⭐️ БЕСПЛАТНО проверить совместимость")
async def compatibility_menu(message: Message, state: FSMContext):
    """
    Показывает меню проверки совместимости.
    """
    user_id = message.from_user.id
    
    # Получаем данные пользователя
    profile = get_user_profile(user_id)
    if not profile:
        await message.answer(
            "Для проверки совместимости необходимо сначала заполнить свой профиль. "
            "Пожалуйста, выберите 'Изменить мои данные' в главном меню."
        )
        return
    
    # Проверяем, сколько у пользователя уже есть активных приглашений
    active_invites_count = count_user_invites(user_id)
    logger.info(f"Пользователь {user_id} запросил меню совместимости. Активных приглашений: {active_invites_count}")
    
    if active_invites_count >= 10:
        logger.warning(f"Пользователь {user_id} достиг лимита приглашений (10/10)")
        await message.answer(
            "⚠️ Вы достигли максимального количества активных приглашений. "
            "Каждому пользователю доступно до 10 бесплатных приглашений для проверки совместимости. "
            "Дождитесь, пока существующие приглашения будут приняты или отклонены, чтобы создать новые."
        )
        return
    
    # Создаем клавиатуру с опциями
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📤 Отправить приглашение", callback_data="send_compatibility_invite")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Мои приглашения", callback_data="my_compatibility_invites")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main_menu")
    )
    
    await message.answer(
        "🔄 Проверка совместимости\n\n"
        "Узнайте, насколько хорошо ваш тип личности по Human Design сочетается с типами "
        "других людей. Отправьте приглашение другу, и когда он примет его и зарегистрируется "
        "в боте, вы оба получите бесплатный анализ вашей совместимости.\n\n"
        "📝 Каждому пользователю доступно до 10 бесплатных приглашений для проверки совместимости.",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "send_compatibility_invite")
async def send_invite_step1(callback: CallbackQuery, state: FSMContext):
    """
    Начинает процесс отправки приглашения, сразу предлагая выбрать тип совместимости.
    """
    await callback.answer()
    
    # Проверяем лимит приглашений
    user_id = callback.from_user.id
    active_invites_count = count_user_invites(user_id)
    logger.info(f"Пользователь {user_id} начал создание приглашения. Активных приглашений: {active_invites_count}")
    
    if active_invites_count >= 10:
        logger.warning(f"Пользователь {user_id} достиг лимита приглашений при попытке создания нового (10/10)")
        await callback.message.answer(
            "⚠️ Вы достигли максимального количества активных приглашений.\n"
            "Каждому пользователю доступно до 10 бесплатных приглашений для проверки совместимости.\n"
            "Дождитесь, пока текущие приглашения будут приняты или отменены, чтобы создать новые."
        )
        return
    
    # Переходим сразу к выбору типа совместимости
    await state.set_state(CompatibilityStates.waiting_for_compatibility_type)
    logger.debug(f"Установлено состояние выбора типа совместимости для пользователя {user_id}")
    
    # Создаем клавиатуру с типами совместимости и для кого они предназначены
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👫 Для друга/подруги", callback_data="comp_type_friendship")
    )
    builder.row(
        InlineKeyboardButton(text="❤️ Для второй половинки", callback_data="comp_type_love")
    )
    builder.row(
        InlineKeyboardButton(text="💼 Для бизнес-партнера", callback_data="comp_type_business")
    )
    builder.row(
        InlineKeyboardButton(text="🔍 Общая совместимость", callback_data="comp_type_general")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Отмена", callback_data="compatibility_menu")
    )
    
    await callback.message.answer(
        "Выберите тип совместимости, который хотите проверить:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("comp_type_"))
async def create_invite_with_type(callback: CallbackQuery, state: FSMContext):
    """
    Создает приглашение с выбранным типом совместимости.
    """
    await callback.answer()
    
    # Получаем выбранный тип совместимости
    compatibility_type = callback.data.split("_")[2]  # comp_type_general -> general
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} выбрал тип совместимости: {compatibility_type}")
    
    # Очищаем состояние
    await state.clear()
    logger.debug(f"Состояние очищено для пользователя {user_id}")
    
    # Определяем описание в зависимости от типа совместимости
    type_descriptions = {
        "general": "общей",
        "love": "любовной",
        "friendship": "дружеской",
        "business": "деловой"
    }
    type_text = type_descriptions.get(compatibility_type, "общей")
    
    # Описание для сохранения в БД
    description = f"Проверка {type_text} совместимости"
    
    # Создаем уникальный код приглашения
    invite_code = create_compatibility_invitation(user_id, description, compatibility_type)
    
    if not invite_code:
        logger.warning(f"Пользователь {user_id} не смог создать приглашение (лимит превышен)")
        await callback.message.answer(
            "⚠️ Вы достигли максимального количества активных приглашений.\n"
            "Каждому пользователю доступно до 10 бесплатных приглашений для проверки совместимости.\n"
            "Дождитесь, пока текущие приглашения будут приняты или отменены, чтобы создать новые."
        )
        return
    
    # Формируем ссылку для приглашения
    invite_link = f"https://t.me/{BOT_USERNAME}?start=comp_{invite_code}"
    logger.info(f"Создано приглашение для проверки {type_text} совместимости: {invite_code}")
    
    # Создаем кнопку для копирования ссылки
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Скопировать ссылку", callback_data=f"copy_comp_link:{invite_code}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="compatibility_menu")
    )
    
    await callback.message.answer(
        f"✅ Приглашение для проверки {type_text} совместимости создано!\n\n"
        f"Отправьте эту ссылку человеку, с которым хотите проверить совместимость:\n"
        f"{invite_link}\n\n"
        f"Как только человек примет приглашение и зарегистрируется в боте, "
        f"вы оба получите бесплатный анализ вашей совместимости.",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "my_compatibility_invites")
async def show_my_invites(callback: CallbackQuery):
    """
    Показывает список приглашений пользователя.
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    invites = get_user_compatibility_invites(user_id)
    logger.info(f"Пользователь {user_id} запросил список своих приглашений. Найдено: {len(invites) if invites else 0}")
    
    if not invites:
        await callback.message.answer(
            "У вас пока нет активных приглашений для проверки совместимости."
        )
        return
    
    # Формируем сообщение со списком приглашений
    msg = "📋 Ваши приглашения для проверки совместимости:\n\n"
    
    for invite in invites:
        status = "✅ Принято" if invite['status'] == 'accepted' else "⏳ Ожидает"
        invite_date = invite['created_at']
        description = invite['description']
        
        msg += f"• {description} - {status} (создано {invite_date})\n"
        
        if invite['status'] == 'accepted':
            msg += f"  Результат анализа отправлен {invite['accepted_at']}\n"
        
        msg += "\n"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="compatibility_menu")
    )
    
    await callback.message.answer(
        msg,
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("copy_comp_link:"))
async def copy_invite_link(callback: CallbackQuery):
    """
    Копирует ссылку приглашения в буфер обмена.
    """
    await callback.answer("Ссылка скопирована!")
    
    invite_code = callback.data.split(":")[1]
    invite_link = f"https://t.me/{BOT_USERNAME}?start=comp_{invite_code}"
    logger.debug(f"Пользователь {callback.from_user.id} скопировал ссылку приглашения: {invite_code}")
    
    await callback.message.answer(
        f"Ссылка приглашения: {invite_link}\n\n"
        "Ссылка скопирована в буфер обмена."
    )

@router.callback_query(F.data == "compatibility_menu")
async def back_to_compatibility_menu(callback: CallbackQuery):
    """
    Возвращает пользователя в меню проверки совместимости.
    """
    await callback.answer()
    logger.debug(f"Пользователь {callback.from_user.id} вернулся в меню совместимости")
    await compatibility_menu(callback.message)

# Функция для обработки принятия приглашения
async def process_compatibility_invitation(message: Message, invite_code: str):
    """
    Обрабатывает принятие приглашения для проверки совместимости.
    
    Args:
        message (Message): Сообщение Telegram
        invite_code (str): Код приглашения
    """
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} пытается принять приглашение: {invite_code}")
    
    # Проверяем, существует ли приглашение и не принято ли оно уже
    invitation = check_compatibility_invitation(invite_code)
    
    if not invitation:
        logger.warning(f"Приглашение {invite_code} не найдено для пользователя {user_id}")
        await message.answer(
            "⚠️ Приглашение не найдено или уже не действительно. "
            "Пожалуйста, запросите новое приглашение."
        )
        return
    
    if invitation['status'] == 'accepted':
        logger.warning(f"Приглашение {invite_code} уже было принято ранее")
        await message.answer(
            "⚠️ Это приглашение уже было принято ранее."
        )
        return
    
    # Получаем профили обоих пользователей
    inviter_id = invitation['user_id']
    inviter_profile = get_user_profile(inviter_id)
    user_profile = get_user_profile(user_id)
    
    if not user_profile:
        logger.warning(f"Пользователь {user_id} не заполнил профиль для принятия приглашения {invite_code}")
        await message.answer(
            "Для проверки совместимости необходимо сначала заполнить свой профиль. "
            "Пожалуйста, завершите регистрацию."
        )
        return
    
    # Отмечаем приглашение как принятое
    accept_compatibility_invitation(invite_code, user_id)
    logger.info(f"Приглашение {invite_code} принято пользователем {user_id}")
    
    # Получаем тип совместимости из приглашения
    compatibility_type = invitation.get('compatibility_type', 'general')
    
    # Текстовое описание типа совместимости
    type_descriptions = {
        "general": "общей",
        "love": "любовной",
        "friendship": "дружеской",
        "business": "деловой"
    }
    type_text = type_descriptions.get(compatibility_type, "общей")
    
    # Сообщаем пользователю, что начинаем анализ
    status_message = await message.answer(f"Выполняем анализ {type_text} совместимости... Это может занять несколько секунд.")
    
    # Получаем данные Human Design для обоих пользователей
    from services.holos_api import send_request_to_holos
    from config import HOLOS_DREAM_URL
    from services.rag_utils import answer_with_rag
    
    # Функция для получения данных через API Holos
    async def get_user_holos_data(profile):
        # Формируем строку даты и времени рождения
        date_str = f"{profile['birth_date']} {profile['birth_time']}"
        latitude = profile["latitude"]
        longitude = profile["longitude"]
        altitude = profile["altitude"]
        
        logger.debug(f"Запрос данных Holos для профиля: {profile['full_name']}, дата: {date_str}, координаты: {latitude}, {longitude}, {altitude}")
        
        # Отправляем запрос к API Holos
        response_data = await send_request_to_holos(
            holos_url=HOLOS_DREAM_URL,
            date_str=date_str,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude
        )
        
        return {
            "user_profile": f"Дата рождения: {profile['birth_date']}\n"
                           f"Время рождения: {profile['birth_time']}\n"
                           f"Место рождения (координаты): {latitude}, {longitude}, {altitude}\n",
            "api_response": response_data
        }
    
    try:
        # Получаем данные для обоих пользователей
        logger.info(f"Получаем данные HD для анализа совместимости пользователей {user_id} и {inviter_id}")
        inviter_holos_data = await get_user_holos_data(inviter_profile)
        user_holos_data = await get_user_holos_data(user_profile)
        
        # Выбираем промпт в зависимости от типа совместимости - используем имена вместо местоимений
        prompts = {
            "general": (
                f"Проанализируй совместимость двух людей по Human Design. Внимательно изучи данные и укажи правильные типы обоих людей в начале анализа.\n\n"
                f"{inviter_profile['full_name']} (создатель приглашения): Дата рождения {inviter_profile['birth_date']}, время {inviter_profile['birth_time']}, координаты {inviter_profile['latitude']}, {inviter_profile['longitude']}.\n"
                f"Данные Human Design {inviter_profile['full_name']}: {inviter_holos_data['api_response']}\n\n"
                f"{user_profile['full_name']} (принявший приглашение): Дата рождения {user_profile['birth_date']}, время {user_profile['birth_time']}, координаты {user_profile['latitude']}, {user_profile['longitude']}.\n"
                f"Данные Human Design {user_profile['full_name']}: {user_holos_data['api_response']}\n\n"
                f"Опиши общую совместимость {inviter_profile['full_name']} и {user_profile['full_name']} во всех сферах жизни. Укажи их сильные и слабые стороны во взаимодействии. Объясни, как их энергетические типы дополняют или конфликтуют друг с другом. Дай конкретные рекомендации для улучшения их взаимодействия.\n\n"
                f"НЕ ВКЛЮЧАЙ в финальный анализ личные данные пользователей (дату рождения, время и координаты). Используй только имена и типы/профили Human Design. При указании типа Human Design для каждого человека, указывай его имя, а не местоимение.\n\n"
                f"В конце анализа добавь: \"Если вы хотите получить более глубокий анализ о себе или взаимоотношениях с другими людьми, перейдите в режим консультации, выбрав в меню кнопку 'Начать консультацию' или 'Выбрать тему консультации'.\""
            ),
            "love": (
                f"Проанализируй любовную/романтическую совместимость двух людей по Human Design. Внимательно изучи данные и укажи правильные типы обоих людей в начале анализа.\n\n"
                f"{inviter_profile['full_name']} (создатель приглашения): Дата рождения {inviter_profile['birth_date']}, время {inviter_profile['birth_time']}, координаты {inviter_profile['latitude']}, {inviter_profile['longitude']}.\n"
                f"Данные Human Design {inviter_profile['full_name']}: {inviter_holos_data['api_response']}\n\n"
                f"{user_profile['full_name']} (принявший приглашение): Дата рождения {user_profile['birth_date']}, время {user_profile['birth_time']}, координаты {user_profile['latitude']}, {user_profile['longitude']}.\n"
                f"Данные Human Design {user_profile['full_name']}: {user_holos_data['api_response']}\n\n"
                f"Сосредоточься на романтической/любовной совместимости {inviter_profile['full_name']} и {user_profile['full_name']}. Опиши, как их энергетические типы взаимодействуют в интимных отношениях. Укажи потенциальные трудности и точки гармонии. Дай конкретные рекомендации для построения здоровых романтических отношений, учитывая особенности их типов. Объясни, как они могут поддерживать баланс и глубокую связь. Отрази особенности их общения, как они сочетаются в интимном плане, оцени по десятибалльной шкале их сочетание.\n\n"
                f"НЕ ВКЛЮЧАЙ в финальный анализ личные данные пользователей (дату рождения, время и координаты). Используй только имена и типы/профили Human Design. При указании типа Human Design для каждого человека, указывай его имя, а не местоимение.\n\n"
                f"В конце анализа добавь: \"Если вы хотите получить более глубокий анализ о себе или взаимоотношениях с другими людьми, перейдите в режим консультации, выбрав в меню кнопку 'Начать консультацию' или 'Выбрать тему консультации'.\""
            ),
            "friendship": (
                f"Проанализируй дружескую совместимость двух людей по Human Design. Внимательно изучи данные и укажи правильные типы обоих людей в начале анализа.\n\n"
                f"{inviter_profile['full_name']} (создатель приглашения): Дата рождения {inviter_profile['birth_date']}, время {inviter_profile['birth_time']}, координаты {inviter_profile['latitude']}, {inviter_profile['longitude']}.\n"
                f"Данные Human Design {inviter_profile['full_name']}: {inviter_holos_data['api_response']}\n\n"
                f"{user_profile['full_name']} (принявший приглашение): Дата рождения {user_profile['birth_date']}, время {user_profile['birth_time']}, координаты {user_profile['latitude']}, {user_profile['longitude']}.\n"
                f"Данные Human Design {user_profile['full_name']}: {user_holos_data['api_response']}\n\n"
                f"Сосредоточься на дружеской совместимости {inviter_profile['full_name']} и {user_profile['full_name']}. Опиши, как их энергетические типы взаимодействуют в дружеских отношениях. Какие общие интересы и занятия могут укрепить их дружбу? Какие потенциальные недопонимания могут возникнуть? Дай конкретные рекомендации для поддержания гармоничной и долгосрочной дружбы, учитывая особенности их типов.\n\n"
                f"НЕ ВКЛЮЧАЙ в финальный анализ личные данные пользователей (дату рождения, время и координаты). Используй только имена и типы/профили Human Design. При указании типа Human Design для каждого человека, указывай его имя, а не местоимение.\n\n"
                f"В конце анализа добавь: \"Если вы хотите получить более глубокий анализ о себе или взаимоотношениях с другими людьми, перейдите в режим консультации, выбрав в меню кнопку 'Начать консультацию' или 'Выбрать тему консультации'.\""
            ),
            "business": (
                f"Проанализируй деловую совместимость двух людей по Human Design. Внимательно изучи данные и укажи правильные типы обоих людей в начале анализа.\n\n"
                f"{inviter_profile['full_name']} (создатель приглашения): Дата рождения {inviter_profile['birth_date']}, время {inviter_profile['birth_time']}, координаты {inviter_profile['latitude']}, {inviter_profile['longitude']}.\n"
                f"Данные Human Design {inviter_profile['full_name']}: {inviter_holos_data['api_response']}\n\n"
                f"{user_profile['full_name']} (принявший приглашение): Дата рождения {user_profile['birth_date']}, время {user_profile['birth_time']}, координаты {user_profile['latitude']}, {user_profile['longitude']}.\n"
                f"Данные Human Design {user_profile['full_name']}: {user_holos_data['api_response']}\n\n"
                f"Сосредоточься на деловой/профессиональной совместимости {inviter_profile['full_name']} и {user_profile['full_name']}. Опиши, как их энергетические типы взаимодействуют в рабочей среде или при совместном бизнесе. Какие роли подходят каждому из них в совместной работе? Как распределить обязанности для максимальной эффективности? Укажи потенциальные конфликты и способы их предотвращения. Дай конкретные рекомендации для продуктивного рабочего партнёрства, учитывая особенности их типов.\n\n"
                f"НЕ ВКЛЮЧАЙ в финальный анализ личные данные пользователей (дату рождения, время и координаты). Используй только имена и типы/профили Human Design. При указании типа Human Design для каждого человека, указывай его имя, а не местоимение.\n\n"
                f"В конце анализа добавь: \"Если вы хотите получить более глубокий анализ о себе или взаимоотношениях с другими людьми, перейдите в режим консультации, выбрав в меню кнопку 'Начать консультацию' или 'Выбрать тему консультации'.\""
            )
        }
        
        # Выбираем нужный промпт или используем промпт для общей совместимости по умолчанию
        query = prompts.get(compatibility_type, prompts["general"])
        
        # Используем RAG для генерации ответа с комбинированными данными (один раз)
        combined_holos_data = {
            "inviter": inviter_holos_data,
            "user": user_holos_data
        }
        
        logger.info(f"Генерация анализа совместимости типа '{compatibility_type}' для пользователей {user_id} и {inviter_id}")
        compatibility_analysis = answer_with_rag(
            query=query,
            holos_data=combined_holos_data,
            mode="free",
            conversation_history="",
            max_tokens=3000
        )
        
        # Удаляем статусное сообщение
        await status_message.delete()
        
        # Отправляем результат обоим пользователям - с индивидуальными преамбулами
        # Сообщение для принявшего приглашение
        logger.info(f"Отправка результата анализа совместимости пользователю {user_id}")
        await message.answer(
            f"✅ Вы приняли приглашение для проверки {type_text} совместимости от пользователя {inviter_profile['full_name']}!\n\n"
            f"Анализ {type_text} совместимости между вами:\n\n"
            f"{compatibility_analysis}"
        )
        
        # Получаем объект бота для отправки сообщения другому пользователю
        bot = message.bot
        
        # Сообщение для создателя приглашения
        logger.info(f"Отправка результата анализа совместимости создателю приглашения {inviter_id}")
        await bot.send_message(
            inviter_id,
            f"✅ Пользователь {user_profile['full_name']} принял ваше приглашение для проверки {type_text} совместимости!\n\n"
            f"Анализ {type_text} совместимости между вами:\n\n"
            f"{compatibility_analysis}"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при анализе совместимости: {str(e)}")
        await status_message.edit_text(f"Произошла ошибка при анализе: {str(e)}")