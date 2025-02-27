"""
Обработчики для работы с платежами через CrystalPay.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.crystalpay import create_payment, check_payment, generate_payment_link
from services.db import activate_subscription, user_has_active_subscription
from config import SUBSCRIPTION_PRICE, SUBSCRIPTION_CURRENCY, SUBSCRIPTION_DURATION_DAYS

router = Router()

# Создаем клавиатуру с кнопкой оплаты
def get_payment_keyboard():
    """
    Создает клавиатуру с кнопкой оплаты подписки.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой оплаты
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Оплатить подписку ({SUBSCRIPTION_PRICE} {SUBSCRIPTION_CURRENCY})",
        callback_data="pay_subscription"
    )
    return builder.as_markup()

@router.message(Command("payment"))
async def cmd_payment(message: Message):
    """
    Обработчик команды /payment.
    Показывает информацию о подписке и кнопку для оплаты.
    
    Args:
        message (Message): Сообщение Telegram
    """
    print("Команда /payment получена")
    
    # Проверяем, есть ли уже активная подписка
    if user_has_active_subscription(message.from_user.id):
        await message.answer("У вас уже есть активная подписка. Спасибо за поддержку!")
        return
    
    # Показываем информацию о подписке и кнопку для оплаты
    await message.answer(
        f"Оформление подписки на {SUBSCRIPTION_DURATION_DAYS} дней\n\n"
        f"Стоимость: {SUBSCRIPTION_PRICE} {SUBSCRIPTION_CURRENCY}\n\n"
        "Подписка дает доступ ко всем функциям бота, включая:\n"
        "• Анализ Human Design\n"
        "• Персональные рекомендации\n"
        "• Неограниченное количество запросов\n\n"
        "Нажмите кнопку ниже для оплаты:",
        reply_markup=get_payment_keyboard()
    )

@router.callback_query(F.data == "pay_subscription")
async def process_payment(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку оплаты.
    Создает платеж в CrystalPay и отправляет ссылку на оплату.
    
    Args:
        callback (CallbackQuery): Callback запрос от Telegram
    """
    await callback.answer("Создаем платеж...")
    
    # Проверяем, есть ли уже активная подписка
    if user_has_active_subscription(callback.from_user.id):
        await callback.message.answer("У вас уже есть активная подписка. Спасибо за поддержку!")
        return
    
    # Создаем платеж в CrystalPay
    success, result = await create_payment(callback.from_user.id)
    
    if success:
        # Получаем данные платежа
        invoice_id = result.get("id", "")
        payment_url = result.get("url", "")  # В API v3 URL возвращается напрямую
        
        # Отправляем пользователю ссылку на оплату
        builder = InlineKeyboardBuilder()
        builder.button(text="Перейти к оплате", url=payment_url)
        builder.button(text="Проверить статус оплаты", callback_data=f"check_payment:{invoice_id}")
        
        await callback.message.answer(
            "Платеж успешно создан!\n\n"
            "Для завершения оплаты перейдите по ссылке ниже. После оплаты "
            "ваша подписка будет автоматически активирована.\n\n"
            "Если вы уже оплатили, но подписка не активировалась, "
            "вы можете проверить статус платежа.",
            reply_markup=builder.as_markup()
        )
    else:
        # В случае ошибки показываем сообщение
        error_message = result.get("error", "Произошла неизвестная ошибка. Пожалуйста, попробуйте позже.")
        
        print(f"Ошибка при создании платежа: {error_message}")
        
        await callback.message.answer(f"Ошибка при создании платежа: {error_message}")

@router.callback_query(F.data.startswith("check_payment:"))
async def check_payment_status(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку проверки статуса платежа.
    Проверяет статус платежа в CrystalPay и активирует подписку, если платеж завершен.
    
    Args:
        callback (CallbackQuery): Callback запрос от Telegram
    """
    await callback.answer("Проверяем статус платежа...")
    
    # Извлекаем ID платежа из callback_data
    invoice_id = callback.data.split(":", 1)[1]
    
    # Проверяем статус платежа в CrystalPay
    success, result = await check_payment(invoice_id)
    
    if success:
        is_paid = result.get("is_paid", False)
        state = result.get("state", "")
        
        if is_paid:
            # Если платеж оплачен, активируем подписку
            user_id = callback.from_user.id
            activate_subscription(user_id)
            
            await callback.message.answer(
                "🎉 Платеж успешно завершен!\n\n"
                f"Ваша подписка активирована на {SUBSCRIPTION_DURATION_DAYS} дней. "
                "Теперь вам доступны все функции бота.\n\n"
                "Спасибо за поддержку!"
            )
        elif state == "pending" or state == "processing":
            # Если платеж еще в ожидании или обработке
            await callback.message.answer(
                "Ваш платеж находится в обработке.\n\n"
                "Это может занять некоторое время в зависимости от выбранного метода оплаты. "
                "Пожалуйста, проверьте статус позже."
            )
        else:
            # Если статус платежа другой (failed и т.д.)
            await callback.message.answer(
                f"Статус платежа: {state}.\n\n"
                "Если у вас возникли проблемы с оплатой, "
                "попробуйте создать новый платеж или обратитесь за поддержкой."
            )
    else:
        # В случае ошибки при проверке платежа
        error_message = result.get("error", "Произошла неизвестная ошибка при проверке платежа.")
        await callback.message.answer(f"Ошибка при проверке платежа: {error_message}")

# Добавим тестовую команду для активации подписки (только для отладки)
@router.message(Command("test_payment"))
async def cmd_test_payment(message: Message):
    """
    Тестовая команда для активации подписки без оплаты.
    Только для тестирования!
    """
    user_id = message.from_user.id
    activate_subscription(user_id)
    await message.answer("Тестовая подписка активирована! Это только для отладки.")

@router.message(Command("pay"))
async def cmd_pay(message: Message):
    """
    Альтернативная команда для /payment.
    """
    await cmd_payment(message)