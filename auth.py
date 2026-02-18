import secrets
from fastapi import Header, HTTPException

from database import get_db


def generate_api_key() -> str:
    return "ta_" + secrets.token_hex(24)


async def create_user(initial_credits: int = 10) -> dict:
    api_key = generate_api_key()
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO users (api_key, credits) VALUES (?, ?)",
            (api_key, initial_credits),
        )
        await db.commit()
        return {"api_key": api_key, "credits": initial_credits}
    finally:
        await db.close()


async def get_user_by_api_key(api_key: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, api_key, credits, created_at FROM users WHERE api_key = ?",
            (api_key,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        await db.close()


async def deduct_credits(api_key: str, amount: int) -> int:
    """Deduct credits and return remaining balance. Raises if insufficient."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, credits FROM users WHERE api_key = ?", (api_key,)
        )
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="Invalid API key")

        current = row["credits"]
        if current < amount:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Required: {amount}, Available: {current}",
            )

        new_balance = current - amount
        await db.execute(
            "UPDATE users SET credits = ? WHERE api_key = ?", (new_balance, api_key)
        )
        await db.commit()
        return new_balance
    finally:
        await db.close()


async def add_credits(api_key: str, amount: int) -> int:
    """Add credits and return new balance."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT credits FROM users WHERE api_key = ?", (api_key,)
        )
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="User not found")

        new_balance = row["credits"] + amount
        await db.execute(
            "UPDATE users SET credits = ? WHERE api_key = ?", (new_balance, api_key)
        )
        await db.commit()
        return new_balance
    finally:
        await db.close()


async def log_usage(
    user_id: int,
    endpoint: str,
    credits_used: int,
    text_length: int,
    detail_level: str,
    language: str,
):
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO usage_logs
               (user_id, endpoint, credits_used, text_length, detail_level, language)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, endpoint, credits_used, text_length, detail_level, language),
        )
        await db.commit()
    finally:
        await db.close()


async def verify_api_key(x_api_key: str = Header(...)) -> dict:
    """FastAPI dependency for API key verification."""
    user = await get_user_by_api_key(x_api_key)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user
