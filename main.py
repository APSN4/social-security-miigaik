import asyncio
import logging
import os
import re
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.session.base import TelegramForbiddenError
from app.constant.app_constant import TOKEN, MAIN_MENU_TEXT, ADMIN_HELP_TEXT, ABOUT_SSO, SSO_TEXT, SEND_ALL_TIMEOUT, \
    FORM_TABLES_REPEAT
from app.constant.app_constant import HELLO_MSG, HELLO_MSG_BUTTONS, HELLO_MSG_IN_BUTTONS
from app.constant.app_constant import FORM_TEXT, FORM_COMPLETED_TEXT, FORM_Q, FORM_TABLES
from app.constant.app_constant import ANY_BUTTONS, DATABASE_NAME, ADMIN_ID

from app.domain.dto.user import User
from config.database import Database

hash_users = {}

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
db = Database(DATABASE_NAME)
bot = Bot(TOKEN)


class AdminStates(StatesGroup):
    WAITING_FOR_FILE = 'waiting_for_file'


class AdminStatesSender(StatesGroup):
    WAITING_FOR_TEXT = 'waiting_for_text'


class TaskForm(StatesGroup):
    pass


for question_index in range(len(FORM_Q)):
    setattr(TaskForm, str(question_index), State())


@dp.message(CommandStart())
async def command_start_handler(message: Message, user_id: int = None) -> None:
    print(HELLO_MSG_IN_BUTTONS)
    builder = InlineKeyboardBuilder()
    for key, value in HELLO_MSG_BUTTONS.items():
        builder.row(types.InlineKeyboardButton(
            text=key, callback_data=value[0])
        )
    builder.row(types.InlineKeyboardButton(
        text=FORM_TEXT, callback_data="form")
    )
    builder.row(types.InlineKeyboardButton(
        text=ABOUT_SSO, callback_data="about")
    )
    user = User(user_id) if user_id else User(message.from_user.id)
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
    await message.answer(answer.replace("\\n", "\n"), reply_markup=builder.as_markup())


@dp.callback_query(lambda call: any(call.data == value[1] for value in ANY_BUTTONS.values()))
async def callback_handler(call: types.CallbackQuery):
    message = call.message
    await message.delete()
    builder = InlineKeyboardBuilder()
    answer = "Выберите значение"
    message_type = None
    files_id = None

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
                case 3:
                    message_type = 3
                    answer = value[3]
                    files_id = value[4]
                    for key_btm, value_btm in value[5].items():
                        builder.row(types.InlineKeyboardButton(
                            text=key_btm, callback_data=value_btm)
                        )
                case 4:
                    message_type = 4
                    answer = value[2]
                    files_id = value[3]

    builder.row(types.InlineKeyboardButton(
        text=MAIN_MENU_TEXT, callback_data="back_to_main_menu")
    )
    await message.answer(answer.replace("\\n", "\n"), reply_markup=builder.as_markup())
    if message_type == 3 or message_type == 4:
        for i in files_id:
            file_path = await db.get_file_data(i)
            await document_send(call, file_path)


async def document_send(call: types.CallbackQuery, file_path):
    file = FSInputFile(path=file_path)
    await bot.send_document(call.from_user.id, document=file)  # caption="Документы для ознакомления"


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
    await message.answer(answer.replace("\\n", "\n"), reply_markup=builder.as_markup())


async def form_results(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    btm_repeat = []

    for index, answer in enumerate(hash_users[call.from_user.id]):  # [0, 1, 0]
        if answer == 0:  # good answer
            btm_index_form = FORM_TABLES[index]  # [3, 4]
            for btm_i_answer in btm_index_form:
                for index_any_btm, (key, value) in enumerate(ANY_BUTTONS.items()):
                    if index_any_btm == btm_i_answer:
                        if FORM_TABLES_REPEAT == 1:
                            builder.row(types.InlineKeyboardButton(
                                text=key, callback_data=value[2])
                            )
                        else:
                            if key not in btm_repeat:
                                builder.row(types.InlineKeyboardButton(
                                    text=key, callback_data=value[2])
                                )
                            btm_repeat.append(key)
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
    user_id = call.from_user.id
    await state.set_state(None)
    await hash_delete_user(call)
    await command_start_handler(call.message, user_id=user_id)


@dp.callback_query(lambda call: call.data == "about")
async def callback_handler(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await hash_delete_user(call)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text=MAIN_MENU_TEXT, callback_data="back_to_main_menu")
    )

    await call.message.answer(SSO_TEXT, reply_markup=builder.as_markup())


@dp.message(Command("admin"))
async def admin_menu(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id in ADMIN_ID:
        command_parts = re.findall(r'\S+', call.text.strip())
        if len(command_parts) <= 1:
            await call.answer(ADMIN_HELP_TEXT)
            return

        argument = command_parts[1]
        if argument == "file":
            await call.answer("Пришлите файл.")
            await state.set_state(AdminStates.WAITING_FOR_FILE)
        elif argument == "delfile":
            try:
                argument_id = command_parts[2]
            except IndexError:
                await call.answer("Укажите ID.")
                return
            is_deleted = await db.delete_file(argument_id)
            if is_deleted:
                await call.answer(f"Запись из БД успешно удалена.\nID: {argument_id}")
            else:
                await call.answer(f"Запись в БД не найдена.\nID: {argument_id}")
        elif argument == "sendall":
            await state.set_state(AdminStatesSender.WAITING_FOR_TEXT)
            await call.answer("Введите текст, который будет отправлен всем.")


@dp.message(lambda message: message.content_type == types.ContentType.TEXT)
async def handle_file(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == AdminStatesSender.WAITING_FOR_TEXT:
        users = await db.get_users()
        argument_text = message.text
        for row in users:
            try:
                await bot.send_message(row[1], argument_text)
                if int(row[1]) != 1:
                    await db.set_active_user(row[1], True)
            except TelegramForbiddenError as e:
                await db.set_active_user(row[1], False)
            await asyncio.sleep(int(SEND_ALL_TIMEOUT))


@dp.message(lambda message: message.content_type == types.ContentType.DOCUMENT)
async def handle_file(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == AdminStates.WAITING_FOR_FILE:
        file_id = message.document.file_id
        file_info = await bot.get_file(file_id)

        file_binary_data = await bot.download_file(file_info.file_path)

        file_name = os.path.basename(file_info.file_path)
        current_directory = os.getcwd()
        folder_path = os.path.join(current_directory, "files")

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'wb') as f:
            f.write(file_binary_data.read())

        file_id = await db.add_file(file_path)
        await message.answer(f"Файл сохранен в системе.\nID: {file_id}")
        await state.clear()


async def main() -> None:
    await db.connect()
    await db.create_table_user()
    await db.create_table_file()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
