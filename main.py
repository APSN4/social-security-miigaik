import ast
import asyncio
import json
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
from dotenv import load_dotenv

# .env
load_dotenv()
TOKEN = getenv("BOT_TOKEN")
MAIN_MENU_TEXT = getenv("MAIN_MENU_TEXT")
HELLO_MSG = getenv("HELLO_MSG").replace("\\n", "\n")
HELLO_MSG_BUTTONS = ast.literal_eval(getenv("HELLO_MSG_BUTTONS"))
HELLO_MSG_IN_BUTTONS = ast.literal_eval(getenv("HELLO_MSG_IN_BUTTONS"))
ANY_BUTTONS = ast.literal_eval(getenv("ANY_BUTTONS"))

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    print(HELLO_MSG_IN_BUTTONS)
    builder = InlineKeyboardBuilder()
    for key, value in HELLO_MSG_BUTTONS.items():
        builder.row(types.InlineKeyboardButton(
            text=key, callback_data=value[0])
        )
    await message.delete()
    await message.answer(HELLO_MSG, reply_markup=builder.as_markup())


@dp.callback_query(lambda call: any(call.data == value[0] for value in HELLO_MSG_IN_BUTTONS.values()))
async def callback_handler(call: types.CallbackQuery):
    message = call.message
    await message.delete()
    builder = InlineKeyboardBuilder()
    answer = "Выберите значение:"
    for key, value in HELLO_MSG_IN_BUTTONS.items():
        if value[0] == call.data:
            builder.row(types.InlineKeyboardButton(
                text=key, callback_data=value[1])
            )
    for key, value in HELLO_MSG_BUTTONS.items():
        if call.data == value[0]:
            answer = value[1]
    builder.row(types.InlineKeyboardButton(
        text=MAIN_MENU_TEXT, callback_data="back_to_main_menu")
    )
    await message.answer(answer, reply_markup=builder.as_markup())


@dp.callback_query(lambda call: any(call.data == value[1] for value in ANY_BUTTONS.values()))
async def callback_handler(call: types.CallbackQuery):
    message = call.message
    await message.delete()
    builder = InlineKeyboardBuilder()
    answer = "Выберите значение"

    for key, value in ANY_BUTTONS.items():
        if value[1] == call.data:
            match value[0]:
                case 0:
                    answer = value[3]
                    for key_btm, value_btm in value[4].items():
                        builder.row(types.InlineKeyboardButton(
                            text=key_btm, callback_data=value_btm)
                        )
                case 1:
                    answer = value[2]

    builder.row(types.InlineKeyboardButton(
        text=MAIN_MENU_TEXT, callback_data="back_to_main_menu")
    )
    await message.answer(answer, reply_markup=builder.as_markup())


@dp.callback_query(lambda call: call.data == "back_to_main_menu")
async def callback_handler(call: types.CallbackQuery):
    await command_start_handler(call.message)

async def main() -> None:
    bot = Bot(TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())