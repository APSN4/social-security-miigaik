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
from app.constant.app_constant import TOKEN, MAIN_MENU_TEXT
from app.constant.app_constant import HELLO_MSG, HELLO_MSG_BUTTONS, HELLO_MSG_IN_BUTTONS
from app.constant.app_constant import FORM_TEXT, FORM_COMPLETED_TEXT, FORM_Q, FORM_TABLES
from app.constant.app_constant import ANY_BUTTONS, DATABASE_NAME

from app.domain.dto.user import User
from config.database import Database

hash_users = {}

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
db = Database(DATABASE_NAME)


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
    user = User(message.from_user.id)
    await db.add_user(user)
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
    index_button = 0
    for value in FORM_Q[answer]:
        builder.row(types.InlineKeyboardButton(
            text=value, callback_data=f"form_btm:{index_button}")
        )
        index_button += 1
    builder.row(types.InlineKeyboardButton(
        text=MAIN_MENU_TEXT, callback_data="back_to_main_menu")
    )
    await message.answer(answer, reply_markup=builder.as_markup())


async def form_results(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()

    for index, answer in enumerate(hash_users[call.from_user.id]):  # [0, 1, 0]
        if answer == 0:  # good answer
            btm_index_form = FORM_TABLES[index]  # [3, 4]
            for btm_i_answer in btm_index_form:
                for index_any_btm, (key, value) in enumerate(ANY_BUTTONS.items()):
                    if index_any_btm == btm_i_answer:
                        builder.row(types.InlineKeyboardButton(
                            text=key, callback_data=value[2])
                        )
    builder.row(types.InlineKeyboardButton(
        text=MAIN_MENU_TEXT, callback_data="back_to_main_menu")
    )
    await call.message.answer(FORM_COMPLETED_TEXT, reply_markup=builder.as_markup())


async def universal_handler(call: types.CallbackQuery, message: types.Message, state: FSMContext):
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
        await hash_delete_user(call)
        await universal_handler(call, message, state)
    try:
        await message.delete()
    except TelegramBadRequest as e:
        print(f"Не удалось удалить сообщение: {e}")


async def hash_add_user(call: types.CallbackQuery, index_button: str):
    if call.from_user.id in hash_users:
        data = hash_users[call.from_user.id]
        data.append(int(index_button))
        hash_users[call.from_user.id] = data
    else:
        hash_users[call.from_user.id] = [int(index_button)]
    print(hash_users)


async def hash_delete_user(call: types.CallbackQuery):
    if call.from_user.id in hash_users:
        del hash_users[call.from_user.id]


@dp.callback_query(lambda call: call.data == "form")
async def callback_handler(call: types.CallbackQuery, state: FSMContext):
    await universal_handler(call, call.message, state)


@dp.callback_query(lambda call: call.data.startswith("form_btm"))
async def callback_handler(call: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()

    data_parts = call.data.split(":")
    index_button = data_parts[1] if len(data_parts) > 1 else None
    await hash_add_user(call, index_button)

    if current_state is None:
        try:
            await call.message.delete()
            await form_results(call)
        except TelegramBadRequest as e:
            print(f"Не удалось удалить сообщение: {e}")
    else:
        await universal_handler(call, call.message, state)


@dp.callback_query(lambda call: call.data == "back_to_main_menu")
async def callback_handler(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await hash_delete_user(call)
    await command_start_handler(call.message)


async def main() -> None:
    bot = Bot(TOKEN)
    await db.connect()
    await db.create_table_user()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
