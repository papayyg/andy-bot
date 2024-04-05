from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated
from aiogram.filters import CommandStart, Command
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, MEMBER, KICKED
from aiogram.fsm.context import FSMContext

from utils.db import chats
from utils.states import Lang
from utils.locales import locales_dict
from utils.commands import set_commands
from keyboards.inline import langs_keyboard
from locales.translations import _
from config import log_chat_id, owner_id

router = Router()

@router.my_chat_member(F.chat.type.in_({"private"}), ChatMemberUpdatedFilter(member_status_changed=KICKED))
@router.my_chat_member(F.chat.type.in_({"private"}), ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_blocked_bot(event: ChatMemberUpdated):
    await chats.change_status(event.from_user.id)


@router.message(Lang.lang)
async def cancel_action(message: Message):
    if not message.new_chat_members:
        await message.answer("Select your language first!")
    

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    if not await chats.chat_exists(message.chat.id):
        await state.set_state(Lang.lang)
        return await message.answer('Select your language to continue:', reply_markup=langs_keyboard)

    await message.answer(await _("00001", locales_dict[message.chat.id]) )
    

@router.message(Command(commands=['help']))
async def help(message: Message):
    lang = locales_dict[message.chat.id]
    await message.answer(await _("help", lang))


@router.message(Command(commands=['github']))
async def github(message: Message):
    await message.answer('Github - https://github.com/papayyg/andy-bot')


@router.message(Command(commands=['issue']))
async def issue(message: Message, bot: Bot):
    lang = locales_dict[message.chat.id]
    if len(message.text) <= 6:
        await message.answer(await _("00036", lang))
    else:
        await bot.send_message(owner_id, f'❗️ Репорт от {message.from_user.mention_html()} (<code>{message.chat.id}</code>): {message.text}')
        await message.answer(await _("00037", lang))


@router.message(Command(commands=['lang']))
async def lang(message: Message, state: FSMContext):
    await state.set_state(Lang.lang)
    await message.answer('Select your language to continue:', reply_markup=langs_keyboard)


@router.callback_query(Lang.lang)
async def register_chat(call: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await call.answer()
    lang = call.data
    chat_id = call.message.chat.id
    locales_dict[chat_id] = lang

    await set_commands(bot, chat_id, lang)

    if await chats.chat_exists(chat_id):
        await chats.change_language(chat_id, lang)
        return await call.message.edit_text(await _("00002", lang))
    
    

    if call.message.chat.type == 'private':
        chat_data = {
            "username": call.message.chat.username,
            "first_name": call.message.chat.first_name,
            "last_name": call.message.chat.last_name,
            "type": 'private',
            "is_blocked": False
        }
        await call.message.edit_text(await _("00001", lang))
    else:
        chat_data = {
            "title": call.message.chat.title,
            "type": call.message.chat.type,
            "is_blocked": False
        }
        bot_chat_member = await bot.get_chat_member(chat_id, bot.id)
        if bot_chat_member.status == "administrator":
            await call.message.edit_text((await _("00031", lang)).format(title=call.message.chat.title))
        else:
            await call.message.edit_text((await _("00030", lang)).format(title=call.message.chat.title))
    chat_data["_id"] = chat_id
    chat_data["lang"] = lang
    await bot.send_message(log_chat_id, str(chat_data))
    await chats.save_chat_data(chat_data)

