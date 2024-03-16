import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from handlers import user_commands

from config import BOT_TOKEN
from utils.locales import get_chats_locales
from utils.commands import set_commands_for_all_chats

async def main():
	bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
	dp = Dispatcher()
	dp.include_routers(
		user_commands.router,
	)
	await get_chats_locales()
	await set_commands_for_all_chats(bot)
	await bot.delete_webhook(drop_pending_updates=True)
	await dp.start_polling(bot)


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, stream=sys.stdout)
	asyncio.run(main())