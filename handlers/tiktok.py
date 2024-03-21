import re

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.media_group import MediaGroupBuilder

from service.tiktok.tiktok import TikTokAPI
from keyboards.inline import commnet_keyboard
from locales.translations import _
from utils.locales import locales_dict

router = Router()

@router.message(F.text.contains('tiktok.com/'))
async def tiktok_message(message: Message):
    ff = await message.answer(await _('00006', locales_dict[message.chat.id]))
    lang = locales_dict[message.chat.id]
    async with TikTokAPI(message) as api:
        if api.type == 'video':
            video = await api.video.download(api.video.download_link)
            caption = await api.video.create_caption()
            keyboard = await api.video.crate_keyboard()
            new_video = await message.answer_video(video, api.video.duration, api.video.width, api.video.height, caption=caption)
            if api.video.second_desc: await message.answer(api.video.second_desc)
            api.video.file_id = new_video.video.file_id
            await api.video.save()

            audio = await api.music.download()
            r = await message.answer_audio(audio, duration=api.music.duration, performer=api.music.author, title=api.music.title, thumbnail=api.music.thumbnail)
            api.music.file_id = r.audio.file_id
            await api.music.save()

        elif api.type == 'profile':
            photo = await api.user.download_cover()
            caption = await api.user.create_caption(lang)
            await message.answer_photo(photo, caption=caption)
        await message.delete()

    await new_video.edit_reply_markup(reply_markup=keyboard)
    await ff.delete()
    
@router.callback_query(F.data.startswith('watermark'))
async def watermark_handler(call: CallbackQuery):
    # await call.answer(await _('00006', locales_dict[call.message.chat.id]))
   
    id = call.data.split("==")[1]
    video, api = await TikTokAPI.video.get_watermark_video(id)
    r = await call.message.answer_video(video, api["duration"], api["width"], api["height"])
    await TikTokAPI.video.save_watermark_id(id, r.video.file_id)

    keyboard = call.message.reply_markup
    del keyboard.inline_keyboard[1]
    await call.message.edit_reply_markup(reply_markup=keyboard)

@router.callback_query(F.data.startswith('stats'))
async def stats_handler(call: CallbackQuery):
    lang = locales_dict[call.message.chat.id]
    id = call.data.split('==')[1]
    text = await TikTokAPI.video.get_stats(id, lang)
    await call.answer(text, show_alert=True)

@router.callback_query(F.data.startswith('profile'))
async def profile_handler(call: CallbackQuery):   
    tt_chain_token = call.data.split('profile==')[1]
    photo, text = await TikTokAPI.user.get_video_profile(tt_chain_token)
    await call.message.answer_photo(photo, caption=text)

    keyboard = call.message.reply_markup
    del keyboard.inline_keyboard[-2][-1]
    await call.message.edit_reply_markup(reply_markup=keyboard)
    
@router.callback_query(F.data.startswith('comments'))
async def comments_handler(call: CallbackQuery):
    id = call.data.split('==')[1]
    text = await TikTokAPI.video.get_comments(id, 5)
    
    new_keyboard = await commnet_keyboard(call.message.chat.id, id)
    await call.message.reply(text, disable_web_page_preview=True, reply_markup=new_keyboard)

    keyboard = call.message.reply_markup
    del keyboard.inline_keyboard[-1]
    await call.message.edit_reply_markup(reply_markup=keyboard)

@router.callback_query(F.data.startswith('more_comments'))
async def more_comments_handler(call: CallbackQuery):
    id = call.data.split('==')[1]
    text = await TikTokAPI.video.get_comments(id, 10)
    await call.message.edit_text(text, disable_web_page_preview=True)
