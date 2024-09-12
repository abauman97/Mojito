import contextlib

import aiosqlite

from mojito import auth


@contextlib.asynccontextmanager
async def get_db():
    # Creates an in-memory test database
    # Creates the admin user and yields a connection
    # async with aiosqlite.connect(":memory:") as conn:
    async with aiosqlite.connect("test.db") as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.cursor()
        await cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	email TEXT NOT NULL UNIQUE,
	password TEXT NOT NULL,
	is_active BOOL NOT NULL
);
""")
        existing_user = await (
            await cursor.execute('select * from users where email = "test@email.com"')
        ).fetchone()
        if not existing_user:
            await cursor.execute(
                f"""
    INSERT INTO users (name, email, password, is_active) VALUES
        (?, ?, ?, ?);                        
    """,
                ("Test User", "test@email.com", auth.hash_password("password"), True),
            )
        cursor = await conn.cursor()
        yield cursor
