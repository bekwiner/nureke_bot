import asyncio
from aiogram import Bot
from aiogram.exceptions import TelegramConflictError
from config import BOT_TOKEN

async def main():
    async with Bot(token=BOT_TOKEN) as bot:
        try:
            updates = await bot.get_updates(limit=10, timeout=0)
            print("updates:", updates)
        except TelegramConflictError as exc:
            print(f"conflict: {exc}")

asyncio.run(main())
