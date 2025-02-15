import asyncio
from contextlib import suppress

from aiogram import Router, Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.enums import DiceEmoji, ParseMode
from aiogram.utils.markdown import hcode
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.requests import (
    insert_user, get_data, start_search, set_balance, give_me_rival, get_rival_id, 
    update_dice_value, get_dice_value, increment_win, increment_losses, increment_tie, 
    reset_game_state, get_balance, update_balance, create_deposit_request, 
    get_pending_deposits, update_deposit_status, create_withdrawal_request
)
from app import keyboard as kb
from app import tron_utils

router = Router()

# Словари для хранения временных данных по депозитам и выводам
deposit_pending = {}
withdraw_pending = {}

@router.message(Command("start"))
async def start_btn(message: Message):
    await message.answer("Ну привет! Готов ебашить? Жми 'НАЧАТЬ', если да", reply_markup=kb.search_kb)
    user = message.from_user.id
    await insert_user(id=user, id2=user)

@router.message(F.text == "Начать поиск")
async def search_btn(message: Message):
    await message.answer("Ищем для тебя соперника. Жди!", reply_markup=kb.back_to_main)
    user = message.from_user.id
    await start_search(id=user, status=1)
    await set_balance(id=user, balance=100)

    async def background_rival_search():
        while True:
            matched = await give_me_rival(id=user)
            if matched:
                await message.answer("Нашелся для тебя соперника. Погнали!", reply_markup=kb.startgame_kb)
                break
            await asyncio.sleep(3)

    asyncio.create_task(background_rival_search())

@router.message(F.text == "Запустить игру")
async def play_btn(message: Message):
    await message.answer("Бросай кубик, епта! Вон кнопка есть для этого. Жмякай ее!", reply_markup=kb.throwdice_kb)

@router.message(F.text == "Кинуть кубик!")
async def throw_button(message: Message):
    user_id_val = message.from_user.id

    balance = await get_balance(user_id=user_id_val)
    if balance <= 0:
        await message.answer("У тебя недостаточно бабок, чтобы играть. Пополни баланс!")
        return

    rival_id_val = await get_rival_id(user_id=user_id_val)
    if not rival_id_val:
        await message.answer("Соперник че-то не найден. Попробуй заново!")
        return

    rival_balance = await get_balance(user_id=rival_id_val)
    if rival_balance <= 0:
        await message.answer("У твоего соперника недостаточно бабок для игры. Игра завершена!")
        await message.bot.send_message(rival_id_val, "У тебя недостаточно баланса для игры. Игра завершена!")
        await reset_game_state(user_id=user_id_val, rival_id=rival_id_val)
        return

    existing_value = await get_dice_value(user_id=user_id_val)
    if existing_value and existing_value != 0:
        await message.answer("Ты уже кинул кубик! Жди, пока соперник кинет свой!")
        return

    dice1_message = await message.answer_dice(emoji="🎲")
    dice2_message = await message.answer_dice(emoji="🎲")
    await asyncio.sleep(3)
    dice1_value = dice1_message.dice.value
    dice2_value = dice2_message.dice.value
    total_value = dice1_value + dice2_value

    await update_dice_value(user_id=user_id_val, dice_value=total_value)
    await message.answer(f"Ты выкинул: {dice1_value} + {dice2_value} = {total_value}")

    rival_value_val = await get_dice_value(user_id=rival_id_val)
    if rival_value_val is None or rival_value_val == 0:
        await message.answer("Ждем, пока твой соперник бросит кубики!")
        return

    if total_value > rival_value_val:
        await message.answer("Победа! Ты выиграл!")
        await message.bot.send_message(rival_id_val, "Ты проиграл! Не фартануло...")
        await update_balance(user_id=user_id_val, points=1)
        await update_balance(user_id=rival_id_val, points=-1)
        await increment_win(user_id=user_id_val)
        await increment_losses(user_id=rival_id_val)
    elif total_value < rival_value_val:
        await message.answer("Ты проиграл! Попробуй еще раз.")
        await message.bot.send_message(rival_id_val, "Поздравляю! Ты выиграл!")
        await update_balance(user_id=user_id_val, points=-1)
        await update_balance(user_id=rival_id_val, points=1)
        await increment_losses(user_id=user_id_val)
        await increment_win(user_id=rival_id_val)
    else:
        await message.answer("Ничья! Удача была равной.")
        await message.bot.send_message(rival_id_val, "Ничья!")
        await increment_tie(user_id=user_id_val)
        await increment_tie(user_id=rival_id_val)

    await update_dice_value(user_id=user_id_val, dice_value=0)
    await update_dice_value(user_id=rival_id_val, dice_value=0)

    new_balance = await get_balance(user_id=user_id_val)
    rival_balance = await get_balance(user_id=rival_id_val)
    await message.answer(f"Твой баланс: {new_balance} очков. Готов продолжить игру?", reply_markup=kb.throwdice_kb)
    await message.bot.send_message(rival_id_val, f"Твой баланс: {rival_balance} очков. Продолжим игру?", reply_markup=kb.throwdice_kb)

@router.message(F.text == "Покинуть игру")
async def leave_game(message: Message):
    user_id_val = message.from_user.id
    rival_id_val = await get_rival_id(user_id=user_id_val)
    if not rival_id_val:
        await message.answer("Ты не в игре! Начни поиск нового соперника!")
        return 
    await message.answer("Ты покинул игру")
    await message.bot.send_message(rival_id_val, "Твой соперник покинул игру!")
    await reset_game_state(user_id=user_id_val, rival_id=rival_id_val)
    await message.answer("Нажми ПОИСК, чтобы найти нового соперника!", reply_markup=kb.search_kb)
    await message.bot.send_message(rival_id_val, "Нажми НАЧАТЬ ПОИСК, чтобы найти нового соперника!", reply_markup=kb.search_kb)

# Обработчики для депозита (пользователь указывает только сумму)
@router.message(F.text == "Депозит")
async def deposit_command(message: Message):
    user_id = message.from_user.id
    deposit_pending[user_id] = {}
    await message.answer("Введите сумму для депозита:")

@router.message(lambda message: message.from_user.id in deposit_pending and 'amount' not in deposit_pending[message.from_user.id])
async def deposit_amount_handler(message: Message):
    user_id = message.from_user.id
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму.")
        return
    deposit_pending[user_id]['amount'] = amount
    await create_deposit_request(playerid=user_id, amount=amount, sender_address="")
    await message.answer(f"Ваш депозит на сумму {amount} USDT зарегистрирован. Ожидайте подтверждения транзакции.")
    del deposit_pending[user_id]

# Обработчики для вывода средств (с уведомлением и для администратора, и для пользователя)
@router.message(F.text == "Вывести")
async def withdraw_command(message: Message):
    user_id = message.from_user.id
    withdraw_pending[user_id] = {}
    await message.answer("Введите USDT TRC20 адрес для вывода:")

@router.message(lambda message: message.from_user.id in withdraw_pending and 'recipient_address' not in withdraw_pending[message.from_user.id])
async def withdraw_address_handler(message: Message):
    user_id = message.from_user.id
    recipient_address = message.text.strip()
    withdraw_pending[user_id]['recipient_address'] = recipient_address
    await message.answer("Введите сумму для вывода:")

@router.message(lambda message: message.from_user.id in withdraw_pending and 'recipient_address' in withdraw_pending[message.from_user.id] and 'amount' not in withdraw_pending[message.from_user.id])
async def withdraw_amount_handler(message: Message):
    user_id = message.from_user.id
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму.")
        return
    balance = await get_balance(user_id)
    if amount > balance:
        await message.answer(f"У вас недостаточно средств. Ваш баланс: {balance} USDT.")
        del withdraw_pending[user_id]
        return
    withdraw_pending[user_id]['amount'] = amount
    recipient_address = withdraw_pending[user_id]['recipient_address']
    txid = await tron_utils.send_usdt(recipient_address, amount)
    if txid:
        await update_balance(user_id, -amount)
        await create_withdrawal_request(playerid=user_id, amount=amount, recipient_address=recipient_address, status="completed", txid=txid)
        new_balance = await get_balance(user_id)
        await message.answer(f"Вывод успешен. TXID: {txid}. Ваш новый баланс: {new_balance} USDT.")
        # Уведомляем администратора о выводе средств
        await message.bot.send_message(206545259, f"Вывод средств: {amount} USDT с кошелька {user_id} отправлен. TXID: {txid}")
    else:
        await message.answer("Ошибка при выводе средств. Попробуйте позже.")
    del withdraw_pending[user_id]

# Фоновая задача для мониторинга депозитов с уведомлением для пользователя и администратора
async def monitor_deposits(bot: Bot):
    while True:
        pending_deposits = await get_pending_deposits()
        for deposit in pending_deposits:
            deposit_id = deposit['id']
            playerid = deposit['playerid']
            amount = deposit['amount']
            txid = await tron_utils.check_deposit_by_amount_async(amount)
            if txid:
                await update_deposit_status(deposit_id, "confirmed", txid)
                await update_balance(playerid, amount)
                # Уведомляем администратора
                await bot.send_message(206545259, f"Депозит зачислен: {amount} USDT с кошелька {playerid}. TXID: {txid}")
                # Уведомляем пользователя
                await bot.send_message(playerid, f"Ваш депозит в размере {amount} USDT успешно зачислен. TXID: {txid}")
        await asyncio.sleep(30)

async def main() -> None:
    bot = Bot(token='7068307478:AAEPTE4OA9uInmFHh0Am-auyy1U-r6mCc_c')
    dp = Dispatcher()
    dp.include_router(router)
    # Передаем экземпляр бота в задачу мониторинга депозитов
    asyncio.create_task(monitor_deposits(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot is switched off')
