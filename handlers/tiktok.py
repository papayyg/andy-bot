import re

from aiogram import Router, F
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.utils.media_group import MediaGroupBuilder

from service.tiktok.tiktok import TikTokAPI
from keyboards.inline import tiktok_video_options, download_videos
from locales.translations import _
from utils.locales import locales_dict

router = Router()

@router.message(F.text.contains('tiktok.com/'))
async def tiktok_message(message: Message):
    async with TikTokAPI(message) as api:
        if api.type == 'video':
            video = await api.video.download(api.video.download_link)
            caption = await api.video.create_caption()
            keyboard = await api.video.crate_keyboard()
            r = await message.answer_video(video, api.video.duration, api.video.width, api.video.height, caption=caption, reply_markup=keyboard)
            if api.video.second_desc: await message.answer(api.video.second_desc)
            api.video.file_id = r.video.file_id
            await api.video.save()
        await message.delete()

@router.callback_query(F.data.startswith('watermark'))
async def watermark_handler(call: CallbackQuery):
    await call.answer(await _('00006', locales_dict[call.message.chat.id]))
    keyboard = call.message.reply_markup
    del keyboard.inline_keyboard[1]
    await call.message.edit_reply_markup(reply_markup=keyboard)

    async with TikTokAPI(call.message) as api:
        pass