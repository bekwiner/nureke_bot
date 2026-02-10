import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config import BOT_TOKEN, SUPERADMIN_IDS
from handlers import router

from handlers import reminder_worker, bonus_code_worker
from database import db

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
        parse_mode=ParseMode.HTML
    )
    await setup_commands(bot)

    dp = Dispatcher()
    dp.include_router(router)

    asyncio.create_task(reminder_worker(bot))
    asyncio.create_task(bonus_code_worker(bot))

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
