import aiosqlite
from sqlite3 import Error, Binary

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

    async def add_user(self, user):
        c = await self.db.cursor()
        await c.execute("SELECT user_id FROM user_status WHERE user_id = ?", (user.get_user_id(),))
        existing_user = await c.fetchone()

        if existing_user:
            return False

        await c.execute("INSERT INTO user_status (user_id, alive) VALUES (?, ?)",
                        (user.get_user_id(), DEFAULT_VALUE_ALIVE,))
        await self.db.commit()
        user_id = c.lastrowid

        return user_id

    async def delete_user(self, user):
        c = await self.db.cursor()
        await c.execute("DELETE FROM user_status WHERE user_id = ?", (user.get_user_id(),))
        await self.db.commit()

    async def get_user(self, user):
        c = await self.db.cursor()
        await c.execute("SELECT * FROM user_status WHERE user_id = ?", (user.get_user_id(),))
        user = await c.fetchone()
        return user

    async def get_users(self):
        c = await self.db.cursor()
        await c.execute("SELECT * FROM user_status")
        users = await c.fetchall()
        return users

    async def set_active_user(self, user_id, active):
        c = await self.db.cursor()
        await c.execute(
            "UPDATE user_status SET alive = ? WHERE user_id = ?",
            (active, user_id)
        )
        await self.db.commit()

    async def create_table_file(self):
        c = await self.db.cursor()
        await c.execute(
            '''CREATE TABLE IF NOT EXISTS files
                (id INTEGER PRIMARY KEY, file_data TEXT)''')
        await self.db.commit()

    async def get_file_data(self, file_id):
        c = await self.db.cursor()
        await c.execute("SELECT file_data FROM files WHERE id=?", (file_id,))
        row = await c.fetchone()
        if row:
            first_result = row[0]
            return first_result
        else:
            return None

    async def delete_file(self, file_id):
        c = await self.db.cursor()

        await c.execute("SELECT COUNT(*) FROM files WHERE id=?", (file_id,))
        row = await c.fetchone()
        file_exists = row[0] > 0 if row else False

        if file_exists:
            await c.execute("DELETE FROM files WHERE id=?", (file_id,))
            await self.db.commit()
            return True
        else:
            return False

    async def add_file(self, file_path):
        c = await self.db.cursor()
        await c.execute("INSERT INTO files (file_data) VALUES (?)", (file_path,))
        await self.db.commit()
        return c.lastrowid

    async def close(self, db):
        try:
            db.close()
            return True
        except Error as err:
            return err
