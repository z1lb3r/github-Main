import asyncio
import aiohttp
from contextlib import suppress

from aiogram import Router, Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.enums import DiceEmoji, ParseMode
from aiogram.utils.markdown import hcode
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums import DiceEmoji
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.requests import (insert_user, get_data, start_search, set_balance, give_me_rival, get_rival_id, 
                          update_dice_value, get_dice_value, increment_win, increment_losses, increment_tie,
                          reset_game_state, get_balance, update_balance, 
                          is_deposit_processed, record_pending_deposit, mark_deposit_processed)
from app import keyboard as kb


router = Router()

#   TRON blockchain configuration
TRON_API_BASE_URL = 'https://api.trongrid.io' 
TRC20_WALLET = 'TGNdiqjoJhwVPFXivbG2GWGV8qoMt2eTs1'
TRON_API_KEY = 'mx0vglYZ55bzK7Yacb'
WITHDRAWAL_PRIVATE_KEY = '7282b73c2cff45e5bd1c9cd06fa76811'


#   States for deposit and withdrawal workflow
class DepositState(StatesGroup):
    waiting_for_amount = State()

class WithdrawalState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_wallet = State()

#   Utility: get the balance of my wallet
async def get_usdt_balance(wallet_address):
    #   Check USDT balance of the specified TRC wallet
    async with aiohttp.ClientSession() as session:
        url = f"{TRON_API_BASE_URL}/v1/accounts/{wallet_address}"
        headers = {"TRON-PRO-API-KEY": TRON_API_KEY}
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            #   Look for the usdt balance in the token list 
            for token in data.get("trc20token_balances", []):
                if token["token_name"] == "Tether USDT":
                    return float(token["balance"]) / 10**6  #   convert from smallest unit 
        return 0

#   Utility: send USDT to external wallet 
async def send_usdt(receiver, amount):
    #   Sends specified amount of USDT to an external wallet
    async with aiohttp.ClientSession() as session:
        url = f"{TRON_API_BASE_URL}/wallet/createtransaction"
        headers = {"Content-Type": "application/json", "TRON-PRO-API-KEY": TRON_API_KEY}
        payload = {
            "owner_address": TRC20_WALLET,
            "to_address": receiver,
            "amount": int(amount * 10**6),
            "asset_name": "Tether USD",
            "privatekey": WITHDRAWAL_PRIVATE_KEY
        }
        async with session.post(url, json=payload, headers=headers) as response:
            return await response.json()


async def background_deposit_search():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{TRON_API_BASE_URL}/v1/accounts/{TRC20_WALLET}/transactions/trc20"
                headers = {"TRON-PRO-API-KEY": TRON_API_KEY}
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        transactions = data.get("data", [])
                        
                        for tx in transactions:
                            if tx["to"] == TRC20_WALLET and tx["token_info"]["symbol"] == "USDT":
                                amount = int(tx["value"]) / (10**6)
                                tx_hash = tx["transaction_id"]
                                
                                # Проверяем, обработан ли депозит
                                if not await is_deposit_processed(tx_hash):
                                    # Регистрируем депозит как "в ожидании"
                                    await record_pending_deposit(tx_id=tx_hash, user_id=None, amount=amount)
                                    
                                    # Логика обработки депозита (например, обновление баланса)
                                    print(f"Pending deposit of {amount} USDT detected for tx: {tx_hash}")
                                    
                                    # После успешного обновления баланса, помечаем транзакцию как обработанную
                                    await mark_deposit_processed(tx_hash)
                                    print(f"Transaction {tx_hash} marked as processed.")
        except Exception as e:
            print(f"Error in deposit detection: {e}")
        
        await asyncio.sleep(30)


async def background_rival_search(user_id: int, message: Message):
    while True:
        rival_id = await give_me_rival(id=user_id)
        if rival_id:
            await message.answer("Соперник найден! Начинаем игру.", reply_markup=kb.startgame_kb)
            break
        await asyncio.sleep(3)


@router.message(Command("start"))
async def start_btn(message:Message):
    await message.answer("Ну привет! Готов ебашить? Жми 'НАЧАТЬ', если да", reply_markup=kb.search_kb)
    user = message.from_user.id
    await insert_user(id=user, id2=user)


@router.message(F.text == "Депозит")
async def start_deposit(message:Message, state:FSMContext):
    await message.answer("Введите сумму USDT, которую хотите внести на депозит")
    await state.set_state(DepositState.waiting_for_amount)
@router.message(DepositState.waiting_for_amount)
async def process_deposit_amount(message:Message, state:FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            await message.answer("Введите положительную сумму для депозита!")
            return
    except ValueError:
        await message.answer("Введите корректное число!")
        return
    
    #   Send USDT trc20 for deposit
    await message.answer(f"Отправьте {amount} USDT на адрес TRC20: '{TRC20_WALLET}'.\n"
                         "Мы проверим перевод и обвновим Ваш баланс.", 
                         parse_mode='Markdown',)
    await state.clear()


@router.message(F.text == "Вывести")
async def start_withdraw(message:Message, state: FSMContext):
    await message.answer("Введите сумму USDT, которую хотите вывести:")
    await state.set_state(WithdrawalState.waiting_for_amount)
@router.message(WithdrawalState.waiting_for_amount)
async def process_withdraw_amount(message:Message, state:FSMContext):
    try:
        amount = float(message.text)
        user_balance = await get_balance(user_id=message.from_user.id)
        if amount <= 0:
            await message.answer("Введите положительное число для вывода!")
            return
        if amount > user_balance:
            await message.answer(f"Недостаточно средств! Ваш баланс: {user_balance}")
            return
    except ValueError:
        await message.answer("Введите корректное число!")
        return

    await state.update_data(amount=amount)
    await message.answer("Введите адрес TRC20 для вывода:")
    await state.set_state(WithdrawalState.waiting_for_wallet)
@router.message(WithdrawalState.waiting_for_wallet)
async def process_withdraw_wallet(message:Message, state:FSMContext):
    wallet_address = message.text.strip()
    #   Check if wallet is correct
    if len(wallet_address) < 34 or not wallet_address.startswith("T"):
        await message.answer("Введён некорректный TRC20-адрес. Попробуйте снова!")
        return
    
    user_data = await state.get_data()
    amount = user_data['amount']

    #   Execute withdrawal
    response = await send_usdt(receiver=wallet_address, amount=amount)
    if response.get("result"):
        await update_balance(user_id=message.from_user.id, points=-amount)
        await message.answer(f"Вывод {amount} USDT успешно выполнен на кошелек {wallet_address}")
    else:
        await message.answer("Ошибка вывода. Попробуй снова")
    await state.clear()


#   Periodically check for deposits
async def detect_and_update_deposits():
    # Periodically check TRC20 wallet for incoming deposits 
    while True:
        current_balance = await get_usdt_balance(TRC20_WALLET)
        await asyncio.sleep(30)


@router.message(F.text == "Начать поиск")
async def search_btn(message:Message):
   await message.answer("Ищем для тебя соперника. Жди!", reply_markup=kb.back_to_main)
   user = message.from_user.id
   await start_search(id=user,status=1)
   await set_balance(id=user, balance=100)
   
   asyncio.create_task(background_rival_search(user_id=user, message=message))

@router.message(F.text == "Запустить игру")
async def play_btn(message:Message):
   await message.answer("Бросай кубик, епта! Вон кнопка есть для этого. Жмякай ее!", reply_markup=kb.throwdice_kb)


@router.message(F.text == "Кинуть кубик!")
async def throw_button(message: Message):
    """Handles dice roll logic."""
    user_id_val = message.from_user.id

    # Check balance for the user
    balance = await get_balance(user_id=user_id_val)
    if balance <= 0:
        await message.answer("У тебя недостаточно бабок, чтобы играть. Пополни баланс!")
        return

    # Check for rival
    rival_id_val = await get_rival_id(user_id=user_id_val)
    if not rival_id_val:
        await message.answer("Соперник че-то не найден. Попробуй заново!")
        return

    # Check balance for the rival
    rival_balance = await get_balance(user_id=rival_id_val)
    if rival_balance <= 0:
        await message.answer("У твоего соперника недостаточно бабок для игры. Игра завершена!")
        await message.bot.send_message(rival_id_val, "У тебя недостаточно баланса для игры. Игра завершена!")
        await reset_game_state(user_id=user_id_val, rival_id=rival_id_val)
        return

    # Check if the user already rolled a dice this round
    existing_value = await get_dice_value(user_id=user_id_val)
    if existing_value and existing_value != 0:
        await message.answer("Ты уже кинул кубик! Жди, пока соперник кинет свой!")
        return

    # Bot rolls 2 dice
    dice1_message = await message.answer_dice(emoji="🎲")
    dice2_message = await message.answer_dice(emoji="🎲")
    await asyncio.sleep(3)  # Wait for animation to complete

    # Calculate total dice value
    dice1_value = dice1_message.dice.value
    dice2_value = dice2_message.dice.value
    total_value = dice1_value + dice2_value

    # Store result in the database
    await update_dice_value(user_id=user_id_val, dice_value=total_value)
    await message.answer(f"Ты выкинул: {dice1_value} + {dice2_value} = {total_value}")

    # Check if rival has already rolled
    rival_value_val = await get_dice_value(user_id=rival_id_val)
    if rival_value_val is None or rival_value_val == 0:
        await message.answer("Ждем, пока твой соперник бросит кубики!")
        return

    # Compare results
    if total_value > rival_value_val:
        await message.answer("Победа! Ты выиграл!")
        await message.bot.send_message(rival_id_val, "Ты проиграл! Не фартануло...")
        await update_balance(user_id=user_id_val, points=1)  # Winner gains 1 point
        await update_balance(user_id=rival_id_val, points=-1)
        await increment_win(user_id=user_id_val)
        await increment_losses(user_id=rival_id_val)
    elif total_value < rival_value_val:
        await message.answer("Ты проиграл! Попробуй еще раз.")
        await message.bot.send_message(rival_id_val, "Поздравляю! Ты выиграл!")
        await update_balance(user_id=user_id_val, points=-1)  # Winner gains 1 point
        await update_balance(user_id=rival_id_val, points=1)
        await increment_losses(user_id=user_id_val)
        await increment_win(user_id=rival_id_val)
    else:
        await message.answer("Ничья! Удача была равной.")
        await message.bot.send_message(rival_id_val, "Ничья!")
        await increment_tie(user_id=user_id_val)
        await increment_tie(user_id=rival_id_val)

    # Reset dice values
    await update_dice_value(user_id=user_id_val, dice_value=0)
    await update_dice_value(user_id=rival_id_val, dice_value=0)

    # Notify players of updated balances
    new_balance = await get_balance(user_id=user_id_val)
    rival_balance = await get_balance(user_id=rival_id_val)
    await message.answer(f"Твой баланс: {new_balance} очков. Готов продолжить игру?", reply_markup=kb.throwdice_kb)
    await message.bot.send_message(rival_id_val, f"Твой баланс: {rival_balance} очков. Продолжим игру?", reply_markup=kb.throwdice_kb)


@router.message(F.text == "Покинуть игру")
async def leave_game(message:Message):
    user_id_val = message.from_user.id
    rival_id_val = await get_rival_id(user_id=user_id_val)

    if not rival_id_val:
        message.answer("Ты не в игре! Начни поиск нового соперника!")
        return 
    
    await message.answer("Ты покинул игру")
    await message.bot.send_message(rival_id_val, "Твой соперник покинул игру!")
    await reset_game_state(user_id=user_id_val, rival_id=rival_id_val)
    await message.answer("Нажми ПОИСК, чтобы найти нового соперника!", reply_markup=kb.search_kb)
    await message.bot.send_message(rival_id_val, "Нажми НАЧАТЬ ПОИСК, чтобы найти нового соперника!", reply_markup=kb.search_kb)

   
async def main() -> None:
    bot = Bot(token='7068307478:AAEPTE4OA9uInmFHh0Am-auyy1U-r6mCc_c')
    dp = Dispatcher()

    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
     asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot is switched off')