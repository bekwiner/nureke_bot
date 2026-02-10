import asyncio
import sqlite3
from datetime import datetime, timezone

from database import db


SQLITE_PATH = "bot.db"


def parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(value)
        except Exception:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def migrate():
    await db.init()

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # USERS
    try:
        cur.execute("SELECT * FROM users")
        rows = cur.fetchall()
    except Exception:
        rows = []
    for r in rows:
        promo_used = r["promo_used"] if "promo_used" in r.keys() else 0
        await db.execute(
            """
            INSERT INTO users (
                user_id, first_name, username, joined_at,
                almaz_balance, bonus_almaz, total_almaz, promo_used
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (user_id) DO NOTHING
            """,
            r["user_id"],
            r["first_name"],
            r["username"],
            parse_dt(r["joined_at"]),
            r["almaz_balance"],
            r["bonus_almaz"],
            r["total_almaz"],
            promo_used,
        )

    # SETTINGS
    try:
        cur.execute("SELECT * FROM settings")
        rows = cur.fetchall()
    except Exception:
        rows = []
    for r in rows:
        await db.execute(
            """
            INSERT INTO settings (key, value)
            VALUES ($1, $2)
            ON CONFLICT (key) DO NOTHING
            """,
            r["key"],
            r["value"],
        )

    # PACKAGES
    try:
        cur.execute("SELECT * FROM packages")
        rows = cur.fetchall()
    except Exception:
        rows = []
    for r in rows:
        await db.execute(
            """
            INSERT INTO packages (id, name, almaz, price, active)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO NOTHING
            """,
            r["id"],
            r["name"],
            r["almaz"],
            r["price"],
            bool(r["active"]),
        )

    # VOUCHERS
    try:
        cur.execute("SELECT * FROM vouchers")
        rows = cur.fetchall()
    except Exception:
        rows = []
    for r in rows:
        await db.execute(
            """
            INSERT INTO vouchers (id, name, almaz, price, active)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO NOTHING
            """,
            r["id"],
            r["name"],
            r["almaz"],
            r["price"],
            bool(r["active"]),
        )


    try:
        cur.execute("SELECT * FROM orders")
        rows = cur.fetchall()
    except Exception:
        rows = []
    for r in rows:
        status = r["status"]
        approved_at = parse_dt(r["updated_at"]) if status == "approved" else None
        rejected_at = parse_dt(r["updated_at"]) if status == "rejected" else None
        await db.execute(
            """
            INSERT INTO orders (
                id, user_id, username, first_name, product_type, product_name,
                almaz, quantity, price, ff_id, check_photo_id, status, admin_id,
                created_at, updated_at, approved_at, rejected_at,
                bonus_code_id, bonus_owner_id, bonus_percent_bp, bonus_amount
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21)
            ON CONFLICT (id) DO NOTHING
            """,
            r["id"],
            r["user_id"],
            r["username"],
            r["first_name"],
            r["product_type"],
            r["product_name"],
            r["almaz"],
            r["quantity"],
            r["price"],
            r["ff_id"],
            r["check_photo_id"],
            r["status"],
            r["admin_id"],
            parse_dt(r["created_at"]),
            parse_dt(r["updated_at"]),
            approved_at,
            rejected_at,
            None,
            None,
            0,
            0,
        )

    # ADMIN LOGS
    try:
        cur.execute("SELECT * FROM admin_logs")
        rows = cur.fetchall()
    except Exception:
        rows = []
    for r in rows:
        await db.execute(
            """
            INSERT INTO admin_logs (id, admin_id, action, order_id, details, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO NOTHING
            """,
            r["id"],
            r["admin_id"],
            r["action"],
            r["order_id"],
            r["details"],
            parse_dt(r["created_at"]),
        )

    # REMINDERS
    try:
        cur.execute("SELECT * FROM reminders")
        rows = cur.fetchall()
    except Exception:
        rows = []
    for r in rows:
        await db.execute(
            """
            INSERT INTO reminders (id, user_id, type, created_at, send_at, sent)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO NOTHING
            """,
            r["id"],
            r["user_id"],
            r["type"],
            parse_dt(r["created_at"]),
            parse_dt(r["send_at"]),
            bool(r["sent"]),
        )

    # PROMOCODES
    try:
        cur.execute("SELECT * FROM promocodes")
        rows = cur.fetchall()
    except Exception:
        rows = []
    for r in rows:
        await db.execute(
            """
            INSERT INTO promocodes (
                id, code, almaz_reward, max_uses, used_count,
                expires_at, active, created_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            ON CONFLICT (id) DO NOTHING
            """,
            r["id"],
            r["code"],
            r["almaz_reward"],
            r["max_uses"],
            r["used_count"],
            parse_dt(r["expires_at"]),
            bool(r["active"]),
            parse_dt(r["created_at"]),
        )

    # PROMOCODE USES
    try:
        cur.execute("SELECT * FROM promocode_uses")
        rows = cur.fetchall()
    except Exception:
        rows = []
    for r in rows:
        await db.execute(
            """
            INSERT INTO promocode_uses (id, promocode_id, user_id, used_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO NOTHING
            """,
            r["id"],
            r["promocode_id"],
            r["user_id"],
            parse_dt(r["used_at"]),
        )

    conn.close()

    # Reset sequences
    await db.execute("SELECT setval(pg_get_serial_sequence('packages','id'), COALESCE(MAX(id), 1)) FROM packages")
    await db.execute("SELECT setval(pg_get_serial_sequence('vouchers','id'), COALESCE(MAX(id), 1)) FROM vouchers")
    await db.execute("SELECT setval(pg_get_serial_sequence('orders','id'), COALESCE(MAX(id), 1)) FROM orders")
    await db.execute("SELECT setval(pg_get_serial_sequence('admin_logs','id'), COALESCE(MAX(id), 1)) FROM admin_logs")
    await db.execute("SELECT setval(pg_get_serial_sequence('promocodes','id'), COALESCE(MAX(id), 1)) FROM promocodes")
    await db.execute("SELECT setval(pg_get_serial_sequence('promocode_uses','id'), COALESCE(MAX(id), 1)) FROM promocode_uses")
    await db.execute("SELECT setval(pg_get_serial_sequence('reminders','id'), COALESCE(MAX(id), 1)) FROM reminders")
    await db.execute("SELECT setval(pg_get_serial_sequence('bonus_codes','id'), COALESCE(MAX(id), 1)) FROM bonus_codes")
    await db.execute("SELECT setval(pg_get_serial_sequence('bonus_code_uses','id'), COALESCE(MAX(id), 1)) FROM bonus_code_uses")

    await db.close()


if __name__ == "__main__":
    asyncio.run(migrate())
