import ast
import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# .env
load_dotenv()
TOKEN = getenv("BOT_TOKEN")
MAIN_MENU_TEXT = getenv("MAIN_MENU_TEXT")
HELLO_MSG = getenv("HELLO_MSG").replace("\\n", "\n")
HELLO_MSG_BUTTONS = ast.literal_eval(getenv("HELLO_MSG_BUTTONS"))
HELLO_MSG_IN_BUTTONS = ast.literal_eval(getenv("HELLO_MSG_IN_BUTTONS"))

FORM_TEXT = getenv("FORM_TEXT")
ANY_BUTTONS = ast.literal_eval(getenv("ANY_BUTTONS"))
FORM_Q = ast.literal_eval(getenv("FORM_Q"))
FORM_TABLES = ast.literal_eval(getenv("FORM_TABLES"))

hash_users = {}

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()


class TaskForm(StatesGroup):
    pass


for question_index in range(len(FORM_Q)):
    setattr(TaskForm, str(question_index), State())


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    print(HELLO_MSG_IN_BUTTONS)
    builder = InlineKeyboardBuilder()
    for key, value in HELLO_MSG_BUTTONS.items():
        builder.row(types.InlineKeyboardButton(
            text=key, callback_data=value[0])
        )
    builder.row(types.InlineKeyboardButton(
        text=FORM_TEXT, callback_data="form")
    )
    try:
        await message.delete()
    except TelegramBadRequest as e:
        print(f"Не удалось удалить сообщение: {e}")
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


async def logic_form(current_state_index, message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    keys = list(FORM_Q.keys())
    answer = keys[current_state_index]
    for value in FORM_Q[answer]:
        builder.row(types.InlineKeyboardButton(
            text=value, callback_data="form_btm")
        )
    builder.row(types.InlineKeyboardButton(
        text=MAIN_MENU_TEXT, callback_data="back_to_main_menu")
    )
    await message.answer(answer, reply_markup=builder.as_markup())

async def universal_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        current_state_index = int(current_state)
        await logic_form(current_state_index, message, state)
        next_state_index = current_state_index + 1
        next_state_name = str(next_state_index)
        if hasattr(TaskForm, next_state_name):
            await state.update_data({current_state: message.text})
            await state.set_state(next_state_name)
        else:
            await state.set_state(None)
    else:
        await state.set_state("0")
        await universal_handler(message, state)
    try:
        await message.delete()
    except TelegramBadRequest as e:
        print(f"Не удалось удалить сообщение: {e}")


@dp.callback_query(lambda call: call.data == "form")
async def callback_handler(call: types.CallbackQuery, state: FSMContext):
    await universal_handler(call.message, state)


@dp.callback_query(lambda call: call.data == "form_btm")
async def callback_handler(call: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if int(current_state) == len(FORM_Q) - 1:
        try:
            await call.message.delete()
            await call.message.answer("Анкета успешно пройдена")
            await command_start_handler(call.message)
        except TelegramBadRequest as e:
            print(f"Не удалось удалить сообщение: {e}")
    else:
        await universal_handler(call.message, state)


@dp.callback_query(lambda call: call.data == "back_to_main_menu")
async def callback_handler(call: types.CallbackQuery):
    await command_start_handler(call.message)


async def main() -> None:
    bot = Bot(TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())