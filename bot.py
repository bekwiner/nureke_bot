import asyncio
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config import BOT_TOKEN, SUPERADMIN_IDS
from handlers import router

from handlers import reminder_worker, bonus_code_worker
from database import db

LOCK_FILE = os.path.join(os.path.dirname(__file__), ".bot.lock")
_lock_fp = None


def acquire_single_instance_lock() -> bool:
    global _lock_fp
    _lock_fp = open(LOCK_FILE, "a+")
    try:
        if os.name == "nt":
            import msvcrt
            _lock_fp.seek(0)
            msvcrt.locking(_lock_fp.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(_lock_fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except Exception:
        _lock_fp.close()
        _lock_fp = None
        return False


def release_single_instance_lock() -> None:
    global _lock_fp
    if not _lock_fp:
        return
    try:
        if os.name == "nt":
            import msvcrt
            _lock_fp.seek(0)
            msvcrt.locking(_lock_fp.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(_lock_fp.fileno(), fcntl.LOCK_UN)
    finally:
        _lock_fp.close()
        _lock_fp = None


async def setup_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Botni ishga tushirish"),
            BotCommand(command="help", description="Yordam"),
            BotCommand(command="balance", description="Balans"),
            BotCommand(command="admin", description="Admin panel"),
        ]
    )

async def main():
    await db.init()
    await db.ensure_superadmins(SUPERADMIN_IDS)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await setup_commands(bot)

    dp = Dispatcher()

    from middlewares.subscription import SubscriptionMiddleware

    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    dp.include_router(router)
    
    asyncio.create_task(reminder_worker(bot))
    asyncio.create_task(bonus_code_worker(bot))

    # Ensure no webhook is active and drop any pending updates
    await bot.delete_webhook(drop_pending_updates=True)

    # If you see TelegramConflictError, it means another polling instance is running.
    # Make sure only one copy of this script is running (stop other terminals/instances).
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    if not acquire_single_instance_lock():
        print("Another bot.py instance is already running. Stop it before starting a new one.")
        sys.exit(1)
    try:
        asyncio.run(main())
    finally:
        release_single_instance_lock()
