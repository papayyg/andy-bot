from aiogram import F, Router, Bot
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, IS_NOT_MEMBER, MEMBER, ADMINISTRATOR, JOIN_TRANSITION, LEAVE_TRANSITION
from aiogram.types import ChatMemberUpdated
from aiogram.fsm.context import FSMContext

from utils.db import chats
from utils.states import Lang
from utils.locales import locales_dict
from keyboards.inline import langs_keyboard
from locales.translations import _

router = Router()

@router.my_chat_member(F.chat.type.in_({"group", "supergroup"}), ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION))
async def bot_deleted_from_group(event: ChatMemberUpdated):
    await chats.change_status(event.chat.id)


@router.my_chat_member(F.chat.type.in_({"group", "supergroup"}), ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> ADMINISTRATOR))
async def bot_added_as_admin(event: ChatMemberUpdated, state: FSMContext):
    if not await chats.chat_exists(event.chat.id):
            await state.set_state(Lang.lang)
            return await event.answer('Select your language to continue:', reply_markup=langs_keyboard)
    await event.answer((await _("00031", locales_dict[event.chat.id])).format(title=event.chat.title))
    

@router.my_chat_member(F.chat.type.in_({"group", "supergroup"}), ChatMemberUpdatedFilter(member_status_changed=MEMBER >> ADMINISTRATOR))
async def bot_got_admin(event: ChatMemberUpdated):
    await event.answer(await _("00032", locales_dict[event.chat.id]))


@router.my_chat_member(F.chat.type.in_({"group", "supergroup"}), ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def bot_added_as_member(event: ChatMemberUpdated, state: FSMContext, bot: Bot):
    chat_info = await bot.get_chat(event.chat.id)
    if chat_info.permissions.can_send_messages:
        if not await chats.chat_exists(event.chat.id):
            await state.set_state(Lang.lang)
            return await event.answer('Select your language to continue:', reply_markup=langs_keyboard)
        await event.answer((await _("00030", locales_dict[event.chat.id])).format(title=event.chat.title))
    else:
        pass

