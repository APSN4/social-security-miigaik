import aiosqlite
from sqlite3 import Error

DEFAULT_VALUE_ALIVE = 1

class Database:
    def __init__(self, database_name):
        self.database_name = database_name
        self.db = None

    async def connect(self):
        try:
            db = await aiosqlite.connect(self.database_name)
            self.db = db
            return db
        except Error as err:
            return err

    async def create_table_user(self):
        c = await self.db.cursor()
        await c.execute(
            "CREATE TABLE IF NOT EXISTS user_status (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, alive BOOLEAN);")
        await self.db.commit()

    async def add_user(self, user) -> bool:
        c = await self.db.cursor()
        await c.execute("SELECT user_id FROM user_status WHERE user_id = ?", (user.get_user_id(),))
        existing_user = await c.fetchone()

        if existing_user:
            return False

        await c.execute("INSERT INTO user_status (user_id, alive) VALUES (?, ?)", (user.get_user_id(), DEFAULT_VALUE_ALIVE,))
        await self.db.commit()
        return True

    async def delete_user(self, user):
        c = await self.db.cursor()
        await c.execute("DELETE FROM user_status WHERE user_id = ?", (user.get_user_id(),))
        await self.db.commit()

    async def get_user(self, user):
        c = await self.db.cursor()
        await c.execute("SELECT * FROM user_status WHERE user_id = ?", (user.get_user_id(),))
        user = await c.fetchone()
        return user

    async def close(self, db):
        try:
            db.close()
            return True
        except Error as err:
            return err
