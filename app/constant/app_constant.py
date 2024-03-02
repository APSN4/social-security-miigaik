import ast
from os import getenv

from dotenv import load_dotenv

# .env
load_dotenv()
TOKEN = getenv("BOT_TOKEN")
MAIN_MENU_TEXT = getenv("MAIN_MENU_TEXT")
HELLO_MSG = getenv("HELLO_MSG").replace("\\n", "\n")
HELLO_MSG_BUTTONS = ast.literal_eval(getenv("HELLO_MSG_BUTTONS"))
HELLO_MSG_IN_BUTTONS = ast.literal_eval(getenv("HELLO_MSG_IN_BUTTONS"))

FORM_TEXT = getenv("FORM_TEXT")
FORM_COMPLETED_TEXT = getenv("FORM_COMPLETED_TEXT")
FORM_Q = ast.literal_eval(getenv("FORM_Q"))
FORM_TABLES = ast.literal_eval(getenv("FORM_TABLES"))

ANY_BUTTONS = ast.literal_eval(getenv("ANY_BUTTONS"))

DATABASE_NAME = getenv("DATABASE_NAME")
