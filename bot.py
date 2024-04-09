import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from handlers import user_commands, tiktok, instagram, groups, errors_handler

from config import BOT_TOKEN, TEST_TOKEN
from utils.locales import get_chats_locales
from utils.commands import set_commands_for_all_chats
from middlewares.antiflood import AntiFloodMiddleware

async def main():
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    dp.message.middleware(AntiFloodMiddleware())

    dp.include_routers(
        user_commands.router,
        tiktok.router,
        instagram.router,
        groups.router,
        errors_handler.router
    )
    await get_chats_locales()
    await set_commands_for_all_chats(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.getLogger('aiogram.event').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())