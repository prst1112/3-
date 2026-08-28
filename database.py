import aiosqlite

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    language TEXT DEFAULT 'ru',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_number TEXT UNIQUE NOT NULL,
    seller_id INTEGER NOT NULL,
    buyer_id INTEGER,
    currency TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    screenshot_file_id TEXT,
    admin_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requisites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS deletion_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id INTEGER NOT NULL,
    requested_by INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    admin_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.executescript(SCHEMA)
        await conn.commit()

        # Аддитивная миграция для уже существующих БД (не пересоздаёт таблицы,
        # просто добавляет недостающие колонки, если их ещё нет).
        cur = await conn.execute("PRAGMA table_info(deals)")
        existing_cols = {row[1] for row in await cur.fetchall()}
        if "card_country" not in existing_cols:
            await conn.execute("ALTER TABLE deals ADD COLUMN card_country TEXT")
        if "card_value" not in existing_cols:
            await conn.execute("ALTER TABLE deals ADD COLUMN card_value TEXT")
        await conn.commit()


# ---------- users ----------

async def get_or_create_user(tg_user) -> dict:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM users WHERE user_id = ?", (tg_user.id,))
        row = await cur.fetchone()

        if row:
            await conn.execute(
                "UPDATE users SET username = ?, full_name = ? WHERE user_id = ?",
                (tg_user.username, tg_user.full_name, tg_user.id),
            )
        else:
            await conn.execute(
                "INSERT INTO users (user_id, username, full_name, language) VALUES (?, ?, ?, 'ru')",
                (tg_user.id, tg_user.username, tg_user.full_name),
            )
        await conn.commit()

        cur = await conn.execute("SELECT * FROM users WHERE user_id = ?", (tg_user.id,))
        row = await cur.fetchone()
        return dict(row)


async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_language(user_id: int, lang: str) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
        await conn.commit()


# ---------- deals ----------

async def create_deal(
    deal_number: str,
    seller_id: int,
    currency: str,
    amount: float,
    description: str,
    card_country: str | None = None,
    card_value: str | None = None,
) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO deals "
            "(deal_number, seller_id, currency, amount, description, status, card_country, card_value) "
            "VALUES (?, ?, ?, ?, ?, 'created', ?, ?)",
            (deal_number, seller_id, currency, amount, description, card_country, card_value),
        )
        await conn.commit()


async def get_deal_by_number(deal_number: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM deals WHERE deal_number = ?", (deal_number,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_deal_by_id(deal_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_deal_buyer(deal_id: int, buyer_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE deals SET buyer_id = ?, status = 'waiting_payment', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (buyer_id, deal_id),
        )
        await conn.commit()


async def update_deal_status(deal_id: int, status: str, admin_id: int | None = None) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        if admin_id is not None:
            await conn.execute(
                "UPDATE deals SET status = ?, admin_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, admin_id, deal_id),
            )
        else:
            await conn.execute(
                "UPDATE deals SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, deal_id),
            )
        await conn.commit()


async def update_deal_screenshot(deal_id: int, file_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE deals SET screenshot_file_id = ? WHERE id = ?", (file_id, deal_id))
        await conn.commit()


async def get_user_stats(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row

        cur = await conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as balance FROM deals WHERE seller_id = ? AND status = 'completed'",
            (user_id,),
        )
        balance = (await cur.fetchone())["balance"]

        cur = await conn.execute(
            "SELECT COUNT(*) as c FROM deals WHERE seller_id = ? AND status = 'completed'", (user_id,)
        )
        sold = (await cur.fetchone())["c"]

        cur = await conn.execute(
            "SELECT COUNT(*) as c FROM deals WHERE buyer_id = ? AND status = 'completed'", (user_id,)
        )
        bought = (await cur.fetchone())["c"]

        return {"balance": balance, "sold": sold, "bought": bought, "total": sold + bought}


# ---------- requisites ----------

async def add_requisite(user_id: int, req_type: str, value: str) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO requisites (user_id, type, value) VALUES (?, ?, ?)",
            (user_id, req_type, value),
        )
        await conn.commit()


async def get_requisites(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM requisites WHERE user_id = ? ORDER BY id", (user_id,))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_requisite_by_id(req_id: int, user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT * FROM requisites WHERE id = ? AND user_id = ?", (req_id, user_id)
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def delete_requisite(req_id: int, user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM requisites WHERE id = ? AND user_id = ?", (req_id, user_id))
        await conn.commit()


# ---------- deletion requests ----------

async def create_deletion_request(deal_id: int, requested_by: int) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            "INSERT INTO deletion_requests (deal_id, requested_by) VALUES (?, ?)",
            (deal_id, requested_by),
        )
        await conn.commit()
        return cur.lastrowid


async def get_deletion_request(req_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM deletion_requests WHERE id = ?", (req_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def update_deletion_request_status(req_id: int, status: str, admin_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE deletion_requests SET status = ?, admin_id = ? WHERE id = ?",
            (status, admin_id, req_id),
        )
        await conn.commit()
