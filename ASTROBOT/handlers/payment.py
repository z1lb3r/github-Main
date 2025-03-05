"""
Обработчики для работы с платежами и балансом через CrystalPay.
Все расчеты ведутся в баллах, где 1 балл = 1 рубль.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.crystalpay import create_payment, check_payment
from services.db import add_to_balance, get_user_balance, get_transaction_history, get_referrals, activate_referral
from config import (
    MIN_REQUIRED_BALANCE,
    REFERRAL_REWARD_USD
)

router = Router()

# Состояния для выбора суммы пополнения
class DepositStates(StatesGroup):
    waiting_for_amount = State()

# Создаем клавиатуру с кнопкой пополнения баланса
def get_deposit_keyboard():
    """
    Создает клавиатуру с кнопкой пополнения баланса.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой пополнения
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💵 Пополнить баланс",
        callback_data="deposit_balance"
    )
    builder.button(
        text="📊 История транзакций",
        callback_data="transaction_history"
    )
    return builder.as_markup()

# Для обратной совместимости
def get_payment_keyboard():
    """
    Создает клавиатуру с кнопкой оплаты для совместимости со старым кодом.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой оплаты
    """
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
        f"📊 Ваш текущий баланс: {balance:.0f} баллов\n\n"
        f"Минимальный баланс для общения с ботом: {MIN_REQUIRED_BALANCE:.0f} баллов\n\n"
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
async def process_deposit_start(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку пополнения баланса.
    Запрашивает у пользователя сумму пополнения.
    
    Args:
        callback (CallbackQuery): Callback запрос от Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    await callback.answer()
    
    # Переходим к состоянию ожидания ввода суммы
    await state.set_state(DepositStates.waiting_for_amount)
    
    await callback.message.answer(
        "Введите сумму пополнения в рублях (от 100 до 10 000 000):"
    )

@router.message(DepositStates.waiting_for_amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    """
    Обработчик ввода суммы пополнения.
    Проверяет корректность введенной суммы и создает платеж.
    
    Args:
        message (Message): Сообщение Telegram
        state (FSMContext): Контекст состояния для FSM
    """
    try:
        # Парсим сумму, заменяя запятые на точки
        amount = int(float(message.text.replace(',', '.').strip()))
        
        # Проверяем ограничения
        if amount < 100:
            await message.answer("⚠️ Минимальная сумма пополнения 100 рублей. Пожалуйста, введите сумму больше.")
            return
        
        if amount > 10000000:
            await message.answer("⚠️ Максимальная сумма пополнения 10 000 000 рублей. Пожалуйста, введите сумму меньше.")
            return
        
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите корректную сумму в рублях (например, 500).")
        return
    
    # Очищаем состояние
    await state.clear()
    
    # Сохраняем сумму для создания платежа
    await process_deposit(message, amount)

async def process_deposit(message_or_callback, deposit_amount=None):
    """
    Создает платеж в CrystalPay и отправляет ссылку на оплату.
    
    Args:
        message_or_callback: Сообщение или Callback
        deposit_amount (int, optional): Сумма пополнения в рублях
    """
    # Определяем, является ли параметр Message или CallbackQuery
    is_callback = hasattr(message_or_callback, 'message')
    
    if is_callback:
        user_id = message_or_callback.from_user.id
        await message_or_callback.answer("Создаем платеж для пополнения баланса...")
        msg_object = message_or_callback.message
    else:
        user_id = message_or_callback.from_user.id
        msg_object = message_or_callback
    
    # Создаем платеж в CrystalPay (в рублях)
    success, result = await create_payment(user_id, deposit_amount)
    
    if success:
        # Получаем данные платежа
        invoice_id = result.get("id", "")
        payment_url = result.get("url", "")
        
        # Отправляем пользователю ссылку на оплату
        builder = InlineKeyboardBuilder()
        builder.button(text="Перейти к оплате", url=payment_url)
        builder.button(text="Проверить статус оплаты", callback_data=f"check_deposit:{invoice_id}:{deposit_amount}")
        
        await msg_object.answer(
            "Платеж для пополнения баланса успешно создан!\n\n"
            "Для завершения оплаты перейдите по ссылке ниже. После оплаты "
            f"ваш баланс будет пополнен на {deposit_amount} баллов.\n\n"
            "Если вы уже оплатили, но баланс не обновился, "
            "вы можете проверить статус платежа.",
            reply_markup=builder.as_markup()
        )
    else:
        # В случае ошибки показываем сообщение
        error_message = result.get("error", "Произошла неизвестная ошибка. Пожалуйста, попробуйте позже.")
        
        print(f"Ошибка при создании платежа: {error_message}")
        
        await msg_object.answer(f"Ошибка при создании платежа: {error_message}")

@router.callback_query(F.data.startswith("check_deposit:"))
async def check_deposit_status(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку проверки статуса платежа.
    Проверяет статус платежа в CrystalPay и пополняет баланс, если платеж завершен.
    
    Args:
        callback (CallbackQuery): Callback запрос от Telegram
    """
    await callback.answer("Проверяем статус платежа...")
    
    # Извлекаем ID платежа и сумму из callback_data
    parts = callback.data.split(":")
    invoice_id = parts[1]
    deposit_amount = int(float(parts[2])) if len(parts) > 2 else 0
    
    # Проверяем статус платежа в CrystalPay
    success, result = await check_payment(invoice_id)
    
    if success:
        is_paid = result.get("is_paid", False)
        state = result.get("state", "")
        
        if is_paid:
            # Если платеж оплачен, пополняем баланс пользователя в баллах
            user_id = callback.from_user.id
            new_balance = add_to_balance(
                user_id, 
                deposit_amount,  # Сумма в баллах равна сумме в рублях
                f"Пополнение баланса через CrystalPay (Invoice ID: {invoice_id})",
                "RUB",  # Оригинальная валюта
                deposit_amount  # Оригинальная сумма
            )
            
            # Проверяем, пришел ли пользователь по реферальной ссылке и активируем её
            referrals = get_referrals(user_id)
            if referrals and any(ref['status'] == 'pending' for ref in referrals):
                # Это активирует реферальную связь и начислит вознаграждение рефереру
                activate_referral(user_id, deposit_amount)
                
                await callback.message.answer(
                    "🎉 Оплата успешно проведена!\n\n"
                    f"Ваш баланс пополнен на {deposit_amount} баллов.\n"
                    f"Текущий баланс: {new_balance:.0f} баллов\n\n"
                    "Вы пришли по реферальной ссылке - ваш реферер получил вознаграждение!"
                )
            else:
                await callback.message.answer(
                    "🎉 Оплата успешно проведена!\n\n"
                    f"Ваш баланс пополнен на {deposit_amount} баллов.\n"
                    f"Текущий баланс: {new_balance:.0f} баллов\n\n"
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
        orig_currency = tx.get("original_currency", "RUB")
        orig_amount = tx.get("original_amount", abs(amount))
        
        # Отображаем сумму транзакции в баллах и в оригинальной валюте, если они разные
        if orig_currency != "RUB":
            message_text += f"• {date}: {tx_type} на сумму {abs(amount):.0f} баллов "
            message_text += f"({abs(orig_amount):.2f} {orig_currency}) - {description}\n\n"
        else:
            message_text += f"• {date}: {tx_type} на сумму {abs(amount):.0f} баллов - {description}\n\n"
    
    await callback.message.answer(message_text)

# Добавим тестовую команду для пополнения баланса (только для отладки)
@router.message(Command("test_deposit"))
async def cmd_test_deposit(message: Message):
    """
    Тестовая команда для пополнения баланса без оплаты.
    Только для тестирования!
    """
    user_id = message.from_user.id
    amount = 500  # Баллы (рубли)
    new_balance = add_to_balance(user_id, amount, "Тестовое пополнение баланса")
    await message.answer(f"Тестовое пополнение на {amount} баллов! Новый баланс: {new_balance:.0f} баллов")

@router.message(Command("pay"))
async def cmd_pay(message: Message):
    """
    Альтернативная команда для /balance.
    """
    await cmd_balance(message)