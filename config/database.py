import aiosqlite
from sqlite3 import Error


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
            "CREATE TABLE IF NOT EXISTS userStatus (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, alive BOOLEAN);")
        await self.db.commit()

    async def add_user(self, user):
        c = await self.db.cursor()
        await c.execute(f"INSERT INTO userStatus ({user}) VALUES ({user})")
        await self.db.commit()

    async def delete_user(self, user_id):
        c = await self.db.cursor()
        await c.execute("DELETE FROM userStatus WHERE user_id = ?", (user_id,))
        await self.db.commit()

    async def get_user(self, user_id):
        c = await self.db.cursor()
        await c.execute("SELECT * FROM userStatus WHERE user_id = ?", (user_id,))
        user = await c.fetchone()
        return user

    async def close(self, db):
        try:
            db.close()
            return True
        except Error as err:
            return err
