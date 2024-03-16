from aiogram import Bot, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from utils.db import chats
from utils.states import Lang
from utils.locales import locales_dict
from utils.commands import set_commands
from keyboards.inline import langs_keyboard
from locales.translations import _

router = Router()

@router.message(Lang.lang)
async def cancel_action(message: Message):
    await message.answer("Select your language first!")
    

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    if not await chats.chat_exists(message.chat.id):
        await state.set_state(Lang.lang)
        return await message.answer('👋 <b><i>Hello!</i></b>\nSelect your language to continue:', reply_markup=langs_keyboard)

    await message.answer(await _("00001", locales_dict[message.chat.id]) )


@router.message(Command(commands=['lang']))
async def start(message: Message, state: FSMContext):
    await state.set_state(Lang.lang)
    await message.answer('👋 <b><i>Hello!</i></b>\nSelect your language to continue:', reply_markup=langs_keyboard)


@router.callback_query(Lang.lang, lambda query: query.data in ['az', 'ru', 'en'])
async def register_chat(call: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()

    lang = call.data
    chat_id = call.message.chat.id
    locales_dict[chat_id] = lang

    await set_commands(bot, chat_id, lang)

    if await chats.chat_exists(chat_id):
        await chats.change_language(chat_id, lang)
        return await call.message.edit_text(await _("00002", lang))
    
    await call.message.edit_text(await _("00001", lang))

    if call.message.chat.type == 'private':
        chat_data = {
            "username": call.message.chat.username,
            "first_name": call.message.chat.first_name,
            "last_name": call.message.chat.last_name,
            "type": 'private',
        }
    else:
        chat_data = {
            "title": call.message.chat.title,
            "type": call.message.chat.type,
        }

    chat_data["_id"] = chat_id
    chat_data["lang"] = lang
    await chats.save_chat_data(chat_data)

