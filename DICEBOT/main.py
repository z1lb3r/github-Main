import asyncio
from contextlib import suppress

from aiogram import Router, Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.enums import DiceEmoji, ParseMode
from aiogram.utils.markdown import hcode
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums import DiceEmoji

from app.requests import insert_user, get_data, start_search, set_balance, give_me_rival, get_rival_id, update_dice_value, get_dice_value, increment_win, increment_losses, increment_tie
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
    """
    1. The bot sends the dice message.
    2. We wait ~3 seconds for the animation to complete.
    3. We store the final dice value in DB.
    4. We compare with the rival's dice.
    """
    user_id_val = message.from_user.id

    # First, check if the user already rolled a dice this round
    existing_value = await get_dice_value(user_id=user_id_val)
    if existing_value is not None and existing_value != 0:
        await message.answer(
            "Ни хуя себе! Ты уже кинул кубик! Жди давай, пока кентишка твой бросит!"
        )
        return

    # 1. Bot sends the dice
    dice_message = await message.answer_dice(emoji="🎲")

    # 2. Wait for the dice animation to finish (about 3 seconds)
    await asyncio.sleep(3)

    # 3. Retrieve final dice value from the bot's own message
    dice_value_val = dice_message.dice.value

    # Store in DB
    await update_dice_value(user_id=user_id_val, dice_value=dice_value_val)
    await message.answer(f"Ты выкинул: {dice_value_val}")

    # 4. Check if we have a rival
    rival_id_val = await get_rival_id(user_id=user_id_val)
    if not rival_id_val:
        await message.answer("Соперник че-то не найден. Попробуй заново! ")
        return

    # Check if the rival has already rolled
    rival_value_val = await get_dice_value(user_id=rival_id_val)
    if not rival_id_val or rival_value_val == 0:
        await message.answer("Ну ждем пока твой соперник кубик бросит!")
        return

    # Compare results
    if dice_value_val > rival_value_val:
        await message.answer("Ни хуя ты кравсавчик! Победа, епта! Втоптал лоха!")
        await message.bot.send_message(rival_id_val, "Не фартануло, брат! Не повезло... :(")
        await increment_win(user_id=user_id_val)
        await increment_losses(user_id=rival_id_val)
    elif dice_value_val < rival_value_val:
        await message.answer("Ну ёбана... Что-то масть не пошла...")
        await message.bot.send_message(rival_id_val, "Опа опа! Госпожа Удача сегодня тебе улыбается в 32 зуба, брат!")
        await increment_losses(user_id=user_id_val)
        await increment_win(user_id=rival_id_val)
    else:
        await message.answer("Господа, да у нас ничья бля!")
        await message.bot.send_message(rival_id_val, "Ничья брат! Жмем ручки, целую в щёчки, кручу сосочки")
        await increment_tie(user_id=user_id_val)
        await increment_tie(user_id=rival_id_val)

   




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