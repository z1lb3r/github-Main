import asyncio
from contextlib import suppress

from aiogram import Router, Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.enums import DiceEmoji, ParseMode
from aiogram.utils.markdown import hcode
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums import DiceEmoji

from app.requests import insert_user, get_data, start_search, set_balance, give_me_rival, get_rival_id, update_dice_value, get_dice_value, increment_win, increment_losses, increment_tie, reset_game_state, get_balance, update_balance
from app import keyboard as kb


router = Router()

@router.message(Command("start"))
async def start_btn(message:Message):
    await message.answer("Ну привет! Готов ебашить? Жми 'НАЧАТЬ', если да", reply_markup=kb.search_kb)
    user = message.from_user.id
    await insert_user(id=user, id2=user)


@router.message(F.text == "Начать поиск")
async def search_btn(message:Message):
   await message.answer("Ищем для тебя соперника. Жди!", reply_markup=kb.back_to_main)
   user = message.from_user.id
   await start_search(id=user,status=1)
   await set_balance(id=user, balance=100)

   async def background_rival_search():
      while True:
         matched = await give_me_rival(id=user)
         if matched:
            await message.answer("Нашелся для тебя соперник. Погнали!", reply_markup=kb.startgame_kb)
            break
         await asyncio.sleep(3)
  
   asyncio.create_task(background_rival_search())


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
