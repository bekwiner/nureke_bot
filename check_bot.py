import asyncio
from aiogram import Bot
from config import BOT_TOKEN

async def main():
    async with Bot(token=BOT_TOKEN) as bot:
        me = await bot.get_me()
        print(me)

asyncio.run(main())
