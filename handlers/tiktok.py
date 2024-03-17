import re

from aiogram import Router, F
from aiogram.types import Message, FSInputFile, CallbackQuery

from service.tiktok import TikTokAPI
from keyboards.inline import tiktok_video_options
from locales.translations import _
from utils.locales import locales_dict
from utils.db.files import save_file, file_exists, add_watermark

router = Router()

@router.message(F.text.contains('tiktok.com/'))
async def tiktok_message(message: Message):
	api = TikTokAPI()
	await api.initialize(message)

	if api.data_type == 'video':
		keyboard = await tiktok_video_options(message.chat.id, api.cover, api.cover_gif, api.link)

		video = api.file_id
		if not api.in_db:
			video = FSInputFile(api.path, api.author)
		
		answer = await message.answer_video(video, api.duration, api.width, api.height, caption=api.caption, reply_markup=keyboard)
		if api.desc_second: await message.answer(api.desc_second)

		await api.save_data_in_db(answer.video.file_id)
		
		await message.delete()
		await api.delete_video()


@router.callback_query(F.data.startswith('watermark'))
async def register_chat(call: CallbackQuery):
	await call.answer(await _('00006', locales_dict[call.message.chat.id]))
	keyboard = call.message.reply_markup
	keyboard.inline_keyboard.pop()
	await call.message.edit_reply_markup(reply_markup=keyboard)

	api = TikTokAPI()
	tiktok_link = call.data.split('==')[1]
	await api.initialize_watermark(call.message, tiktok_link)

	video = api.watermark
	if not api.watermark:
		video = FSInputFile(api.path, api.file_name)

	answer = await call.message.answer_video(video, api.duration, api.width, api.height)
	await api.save_data_in_db(answer.video.file_id)

	await api.delete_video()
