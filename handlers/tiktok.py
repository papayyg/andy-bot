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
        if api.data_type == 'video':
            await api.video.download(api.video.download_link)
            caption = await api.video.create_caption()
            video = FSInputFile(api.path, api.author.unique_name)
            await message.answer_video(video, api.video.duration, api.video.width, api.video.height, caption=caption)
            if api.video.second_desc: await message.answer(api.video.second_desc)
