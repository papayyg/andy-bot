from aiogram.types import BotCommand, BotCommandScopeChat

from locales.translations import _
from utils.locales import locales_dict

async def get_commands(lang):
    commands = [
        BotCommand(
            command='help',
            description=await _('cmd1', lang)
        ),
        BotCommand(
            command='lang',
            description=await _('cmd2', lang)
        ),
        BotCommand(
            command='start',
            description=await _('cmd3', lang)
        ),
    ]
    return commands


async def set_commands(bot, chat_id, lang):
    command = await get_commands(lang)
    await bot.set_my_commands(command, BotCommandScopeChat(chat_id=chat_id))


async def set_commands_for_all_chats(bot):
    for chat_id, lang in locales_dict.items():
        try:
            await set_commands(bot, chat_id, lang)
        except Exception as ex:
            print(f'Error in commands_set: {ex}')