import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "text_api.db")


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    db = await get_db()
    try:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT UNIQUE NOT NULL,
                credits INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                endpoint TEXT NOT NULL,
                credits_used INTEGER NOT NULL,
                text_length INTEGER NOT NULL,
                detail_level TEXT NOT NULL DEFAULT 'basic',
                language TEXT NOT NULL DEFAULT 'en',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id)
        """)
        await db.commit()
    finally:
        await db.close()
