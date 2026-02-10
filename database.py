import os
from datetime import datetime, timezone

import asyncpg


DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/zoniks_bot"
try:
    from config import DATABASE_URL as CONFIG_DATABASE_URL
except Exception:
    CONFIG_DATABASE_URL = None

DATABASE_URL = os.getenv("DATABASE_URL", CONFIG_DATABASE_URL or DEFAULT_DATABASE_URL)


class Database:
    def __init__(self) -> None:
        self.pool: asyncpg.Pool | None = None

    async def init(self) -> None:
        if self.pool:
            return
        self.pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=60,
        )
        await self._init_schema()

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def executemany(self, query: str, args_list: list[tuple]):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(query, args_list)

    async def fetch(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def _init_schema(self) -> None:
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                joined_at TIMESTAMPTZ,

                almaz_balance INTEGER DEFAULT 0,
                bonus_almaz INTEGER DEFAULT 0,
                total_almaz INTEGER DEFAULT 0,
                promo_used INTEGER DEFAULT 0
            )
            """
        )
        await self.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS promo_used INTEGER DEFAULT 0"
        )

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS packages (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                almaz INTEGER NOT NULL,
                price INTEGER NOT NULL,
                active BOOLEAN DEFAULT TRUE
            )
            """
        )

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS vouchers (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                almaz INTEGER NOT NULL,
                price INTEGER NOT NULL,
                active BOOLEAN DEFAULT TRUE
            )
            """
        )

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id BIGSERIAL PRIMARY KEY,

                user_id BIGINT NOT NULL,
                username TEXT,
                first_name TEXT,

                product_type TEXT,
                product_name TEXT,

                almaz INTEGER,
                quantity INTEGER DEFAULT 1,
                price INTEGER,

                ff_id TEXT,
                check_photo_id TEXT,

                status TEXT DEFAULT 'pending',
                admin_id BIGINT,

                bonus_code_id BIGINT,
                bonus_owner_id BIGINT,
                bonus_percent_bp INTEGER DEFAULT 0,
                bonus_amount INTEGER DEFAULT 0,

                created_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ,
                approved_at TIMESTAMPTZ,
                rejected_at TIMESTAMPTZ,
                channel_posted_at TIMESTAMPTZ
            )
            """
        )
        await self.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS bonus_code_id BIGINT")
        await self.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS bonus_owner_id BIGINT")
        await self.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS bonus_percent_bp INTEGER DEFAULT 0")
        await self.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS bonus_amount INTEGER DEFAULT 0")
        await self.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ")
        await self.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMPTZ")
        await self.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS channel_posted_at TIMESTAMPTZ")

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_logs (
                id BIGSERIAL PRIMARY KEY,

                admin_id BIGINT NOT NULL,
                action TEXT NOT NULL,
                order_id BIGINT,

                details TEXT,
                created_at TIMESTAMPTZ
            )
            """
        )

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_order_messages (
                order_id BIGINT NOT NULL,
                admin_id BIGINT NOT NULL,
                message_id BIGINT NOT NULL,
                caption TEXT,
                created_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ,
                PRIMARY KEY (order_id, admin_id)
            )
            """
        )

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS withdraw_requests (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                amount INTEGER NOT NULL,
                ff_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMPTZ,
                processed_at TIMESTAMPTZ,
                processed_by BIGINT,
                note TEXT,
                channel_posted_at TIMESTAMPTZ
            )
            """
        )
        await self.execute("ALTER TABLE withdraw_requests ADD COLUMN IF NOT EXISTS channel_posted_at TIMESTAMPTZ")

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS withdraw_notifications (
                request_id BIGINT NOT NULL,
                admin_id BIGINT NOT NULL,
                message_id BIGINT NOT NULL,
                created_at TIMESTAMPTZ,
                PRIMARY KEY (request_id, admin_id)
            )
            """
        )

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS payment_cards (
                id BIGSERIAL PRIMARY KEY,
                card_number TEXT NOT NULL,
                holder_name TEXT,
                bank_name TEXT,
                active BOOLEAN DEFAULT FALSE,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ
            )
            """
        )

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS order_log_notifications (
                order_id BIGINT NOT NULL,
                status TEXT NOT NULL,
                sent_at TIMESTAMPTZ,
                PRIMARY KEY (order_id, status)
            )
            """
        )

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                type TEXT,
                created_at TIMESTAMPTZ,
                send_at TIMESTAMPTZ,
                sent BOOLEAN DEFAULT FALSE
            )
            """
        )

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS promocodes (
                id BIGSERIAL PRIMARY KEY,

                code TEXT UNIQUE NOT NULL,
                almaz_reward INTEGER NOT NULL,
                max_uses INTEGER NOT NULL,
                used_count INTEGER DEFAULT 0,

                expires_at TIMESTAMPTZ,
                active BOOLEAN DEFAULT TRUE,
                is_deleted BOOLEAN DEFAULT FALSE,

                created_at TIMESTAMPTZ
            )
            """
        )
        await self.execute("ALTER TABLE promocodes ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE")

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS promocode_uses (
                id BIGSERIAL PRIMARY KEY,

                promocode_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,

                used_at TIMESTAMPTZ,

                UNIQUE(promocode_id, user_id)
            )
            """
        )

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                user_id BIGINT PRIMARY KEY,
                role TEXT NOT NULL,
                active BOOLEAN DEFAULT TRUE,
                created_by BIGINT,
                created_at TIMESTAMPTZ
            )
            """
        )
        await self.execute("ALTER TABLE admins ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE")
        await self.execute("ALTER TABLE admins ADD COLUMN IF NOT EXISTS created_by BIGINT")
        await self.execute("ALTER TABLE admins ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ")

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS bonus_codes (
                id BIGSERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                owner_id BIGINT NOT NULL,
                created_at TIMESTAMPTZ,
                expires_at TIMESTAMPTZ,
                active BOOLEAN DEFAULT TRUE,
                total_uses INTEGER DEFAULT 0,
                total_bonus INTEGER DEFAULT 0,
                expired_notified BOOLEAN DEFAULT FALSE
            )
            """
        )
        await self.execute("ALTER TABLE bonus_codes ADD COLUMN IF NOT EXISTS expired_notified BOOLEAN DEFAULT FALSE")

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS bonus_code_uses (
                id BIGSERIAL PRIMARY KEY,
                code_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                use_count INTEGER DEFAULT 0,
                cycle_start_at TIMESTAMPTZ,
                last_used_at TIMESTAMPTZ,
                UNIQUE(code_id, user_id)
            )
            """
        )

        await self.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uniq_active_bonus_code
            ON bonus_codes (owner_id)
            WHERE active = TRUE
            """
        )

        await self.execute(
            """
            INSERT INTO settings (key, value)
            VALUES ($1, $2)
            ON CONFLICT (key) DO NOTHING
            """,
            "prices_text",
            "💎 ALMAZ NARXLARI\n\n"
            "200 💎 — 24 000 so‘m\n"
            "420 💎 — 48 000 so‘m\n"
            "850 💎 — 96 000 so‘m\n\n"
            "⏱ Yetkazish: 5–60 daqiqa\n"
            "🔒 100% xavfsiz",
        )

        await self.execute(
            """
            INSERT INTO settings (key, value)
            VALUES ($1, $2)
            ON CONFLICT (key) DO NOTHING
            """,
            "admin_contact_text",
            "📞 Admin bilan bog‘lanish\n\n"
            "Agar savollaringiz bo‘lsa, quyidagi admin bilan bog‘laning:\n\n"
            "👤 Admin: @your_admin_username\n"
            "⏱ Ish vaqti: 09:00 – 23:00",
        )

        await self.execute(
            """
            INSERT INTO settings (key, value)
            VALUES ($1, $2)
            ON CONFLICT (key) DO NOTHING
            """,
            "main_menu_photo_id",
            "",
        )

        await self.execute(
            """
            INSERT INTO settings (key, value)
            VALUES ($1, $2)
            ON CONFLICT (key) DO NOTHING
            """,
            "bot_bonus_balance",
            "0",
        )

        packages_count = await self.fetchval("SELECT COUNT(*) FROM packages")
        if packages_count == 0:
            await self.executemany(
                "INSERT INTO packages (name, almaz, price) VALUES ($1, $2, $3)",
                [
                    ("200 💎", 200, 24000),
                    ("420 💎", 420, 48000),
                    ("850 💎", 850, 96000),
                ],
            )

        vouchers_count = await self.fetchval("SELECT COUNT(*) FROM vouchers")
        if vouchers_count == 0:
            await self.executemany(
                "INSERT INTO vouchers (name, almaz, price) VALUES ($1, $2, $3)",
                [
                    ("💳 Haftalik voucher", 450, 17000),
                    ("💳 Oylik voucher", 2600, 110000),
                ],
            )

    async def ensure_superadmins(self, user_ids: list[int]) -> None:
        now = utc_now()
        for user_id in user_ids:
            await self.execute(
                """
                INSERT INTO admins (user_id, role, active, created_by, created_at)
                VALUES ($1, 'superadmin', TRUE, $2, $3)
                ON CONFLICT (user_id)
                DO UPDATE SET role = 'superadmin', active = TRUE
                """,
                user_id,
                user_id,
                now,
            )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


db = Database()
