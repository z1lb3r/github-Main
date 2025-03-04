"""
Обработчики для работы с платежами и балансом через CrystalPay.
Все расчеты ведутся в USD, хотя оплата может быть в разных валютах.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.crystalpay import create_payment, check_payment
from services.db import add_to_balance, get_user_balance, get_transaction_history, get_referrals, activate_referral
from config import (
    DEPOSIT_AMOUNT_USD, 
    DEPOSIT_AMOUNT_RUB, 
    DISPLAY_CURRENCY, 
    MIN_REQUIRED_BALANCE,
    REFERRAL_REWARD_USD
)

router = Router()

# Создаем клавиатуру с кнопкой пополнения баланса
def get_deposit_keyboard():
    """
    Создает клавиатуру с кнопкой пополнения баланса.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой пополнения
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Пополнить баланс на ${DEPOSIT_AMOUNT_USD:.2f}",
        callback_data="deposit_balance"
    )
    builder.button(
        text="История транзакций",
        callback_data="transaction_history"
    )
    return builder.as_markup()

# Здесь нужно добавить (или переименовать) функцию get_payment_keyboard
def get_payment_keyboard():
    """
    Создает клавиатуру с кнопкой оплаты для совместимости со старым кодом.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой оплаты
    """
    # Просто используем функцию get_deposit_keyboard для совместимости
    return get_deposit_keyboard()

@router.message(Command("balance"))
async def cmd_balance(message: Message):
    """
    Обработчик команды /balance.
    Показывает текущий баланс пользователя и кнопку для пополнения.
    
    Args:
        message (Message): Сообщение Telegram
    """
    print("Команда /balance получена")
    
    # Получаем текущий баланс пользователя
    balance = get_user_balance(message.from_user.id)
    
    # Показываем информацию о балансе и кнопку для пополнения
    await message.answer(
        f"📊 Ваш текущий баланс: ${balance:.2f}\n\n"
        f"Минимальный баланс для общения с ботом: ${MIN_REQUIRED_BALANCE:.2f}\n\n"
        "Для пополнения баланса нажмите кнопку ниже:",
        reply_markup=get_payment_keyboard()
    )

@router.message(Command("payment"))
async def cmd_payment(message: Message):
    """
    Обработчик команды /payment.
    Переадресует на команду /balance для обратной совместимости.
    
    Args:
        message (Message): Сообщение Telegram
    """
    print("Команда /payment получена, переадресация на /balance")
    await cmd_balance(message)

@router.callback_query(F.data == "deposit_balance")
async def process_deposit(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку пополнения баланса.
    Создает платеж в CrystalPay и отправляет ссылку на оплату.
    
    Args:
        callback (CallbackQuery): Callback запрос от Telegram
    """
    await callback.answer("Создаем платеж для пополнения баланса...")
    
    # Создаем платеж в CrystalPay (в рублях)
    success, result = await create_payment(callback.from_user.id)
    
    if success:
        # Получаем данные платежа
        invoice_id = result.get("id", "")
        payment_url = result.get("url", "")
        
        # Отправляем пользователю ссылку на оплату
        builder = InlineKeyboardBuilder()
        builder.button(text="Перейти к оплате", url=payment_url)
        builder.button(text="Проверить статус оплаты", callback_data=f"check_deposit:{invoice_id}")
        
        await callback.message.answer(
            "Платеж для пополнения баланса успешно создан!\n\n"
            "Для завершения оплаты перейдите по ссылке ниже. После оплаты "
            f"ваш баланс будет пополнен на ${DEPOSIT_AMOUNT_USD:.2f}.\n\n"
            "Если вы уже оплатили, но баланс не обновился, "
            "вы можете проверить статус платежа.",
            reply_markup=builder.as_markup()
        )
    else:
        # В случае ошибки показываем сообщение
        error_message = result.get("error", "Произошла неизвестная ошибка. Пожалуйста, попробуйте позже.")
        
        print(f"Ошибка при создании платежа: {error_message}")
        
        await callback.message.answer(f"Ошибка при создании платежа: {error_message}")

@router.callback_query(F.data.startswith("check_deposit:"))
async def check_deposit_status(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку проверки статуса платежа.
    Проверяет статус платежа в CrystalPay и пополняет баланс, если платеж завершен.
    
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
            # Если платеж оплачен, пополняем баланс пользователя в USD
            user_id = callback.from_user.id
            new_balance = add_to_balance(
                user_id, 
                DEPOSIT_AMOUNT_USD,  # Сумма в USD
                f"Пополнение баланса через CrystalPay (Invoice ID: {invoice_id})",
                "RUB",  # Оригинальная валюта
                DEPOSIT_AMOUNT_RUB   # Оригинальная сумма
            )
            
            # Проверяем, пришел ли пользователь по реферальной ссылке и активируем её
            referrals = get_referrals(user_id)
            if referrals and any(ref['status'] == 'pending' for ref in referrals):
                # Это активирует реферальную связь и начислит вознаграждение рефереру
                activate_referral(user_id, DEPOSIT_AMOUNT_USD)
                
                await callback.message.answer(
                    "🎉 Оплата успешно проведена!\n\n"
                    f"Ваш баланс пополнен на ${DEPOSIT_AMOUNT_USD:.2f}.\n"
                    f"Текущий баланс: ${new_balance:.2f}\n\n"
                    "Вы пришли по реферальной ссылке - ваш реферер получил вознаграждение!"
                )
            else:
                await callback.message.answer(
                    "🎉 Оплата успешно проведена!\n\n"
                    f"Ваш баланс пополнен на ${DEPOSIT_AMOUNT_USD:.2f}.\n"
                    f"Текущий баланс: ${new_balance:.2f}\n\n"
                    "Теперь вы можете использовать бота."
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

@router.callback_query(F.data == "transaction_history")
async def show_transaction_history(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку истории транзакций.
    Показывает историю транзакций пользователя.
    
    Args:
        callback (CallbackQuery): Callback запрос от Telegram
    """
    await callback.answer("Получаем историю транзакций...")
    
    # Получаем историю транзакций пользователя
    transactions = get_transaction_history(callback.from_user.id)
    
    if not transactions:
        await callback.message.answer("У вас пока нет истории транзакций.")
        return
    
    # Формируем сообщение с историей транзакций
    message_text = "📜 История транзакций:\n\n"
    
    for tx in transactions:
        tx_type = "пополнение" if tx["type"] == "deposit" else "списание"
        amount = tx["amount"]
        date = tx["created_at"]
        description = tx["description"]
        orig_currency = tx.get("original_currency", "USD")
        orig_amount = tx.get("original_amount", abs(amount))
        
        # Отображаем сумму транзакции в USD и в оригинальной валюте, если они разные
        if orig_currency != "USD":
            message_text += f"• {date}: {tx_type} на сумму ${abs(amount):.2f} "
            message_text += f"({abs(orig_amount):.2f} {orig_currency}) - {description}\n\n"
        else:
            message_text += f"• {date}: {tx_type} на сумму ${abs(amount):.2f} - {description}\n\n"
    
    await callback.message.answer(message_text)

# Добавим тестовую команду для пополнения баланса (только для отладки)
@router.message(Command("test_deposit"))
async def cmd_test_deposit(message: Message):
    """
    Тестовая команда для пополнения баланса без оплаты.
    Только для тестирования!
    """
    user_id = message.from_user.id
    amount = DEPOSIT_AMOUNT_USD
    new_balance = add_to_balance(user_id, amount, "Тестовое пополнение баланса")
    await message.answer(f"Тестовое пополнение на ${amount:.2f}! Новый баланс: ${new_balance:.2f}")

@router.message(Command("pay"))
async def cmd_pay(message: Message):
    """
    Альтернативная команда для /balance.
    """
    await cmd_balance(message)