import re

from aiogram import Router, F
from aiogram.types import Message, FSInputFile, CallbackQuery

from service.tiktok import TikTokAPI
from keyboards.inline import tiktok_video_options, download_videos
from locales.translations import _
from utils.locales import locales_dict

router = Router()

@router.message(F.text.contains('tiktok.com/'))
async def tiktok_message(message: Message):

	lang = locales_dict[message.chat.id]
	api = TikTokAPI(lang)
	await api.initialize(message)

	if api.data_type == 'video':
		keyboard = await tiktok_video_options(message.chat.id, api.cover, api.cover_gif, api.link)

		video = api.file_id if api.in_db else FSInputFile(api.path, api.author)
		answer = await message.answer_video(video, api.duration, api.width, api.height, caption=api.caption, reply_markup=keyboard)
		if api.desc_second: await message.answer(api.desc_second)

		await api.save_data_in_db(answer.video.file_id)
	
	elif api.data_type == 'profile':
		keyboard = await download_videos(message.chat.id, api.link)
		photo = FSInputFile(api.path, api.author)
		await message.answer_photo(photo, api.caption, reply_markup=keyboard)
		

	await message.delete()
	await api.delete_file()


@router.callback_query(F.data.startswith('watermark'))
async def watermark_handler(call: CallbackQuery):
	await call.answer(await _('00006', locales_dict[call.message.chat.id]))
	keyboard = call.message.reply_markup
	del keyboard.inline_keyboard[1]
	await call.message.edit_reply_markup(reply_markup=keyboard)

	lang = locales_dict[call.message.chat.id]
	api = TikTokAPI(lang)
	tiktok_link = call.data.split('==')[1]
	api.watermark = tiktok_link
	await api.initialize_watermark(call.message, tiktok_link)

	video = api.watermark_id if api.watermark_id else FSInputFile(api.path, api.file_name)
	answer = await call.message.answer_video(video, api.duration, api.width, api.height) 
	await api.save_data_in_db(answer.video.file_id)

	await api.delete_file()


@router.callback_query(F.data.startswith('stats'))
async def stats_handler(call: CallbackQuery):
	lang = locales_dict[call.message.chat.id]
	api = TikTokAPI(lang)
	tiktok_link = call.data.split('==')[1]
	text = await api.get_stats(tiktok_link)
	await call.answer(text, show_alert=True)


@router.callback_query(F.data.startswith('profile'))
async def profile_handler(call: CallbackQuery):
	await call.answer(await _('00006', locales_dict[call.message.chat.id]))
	keyboard = call.message.reply_markup
	del keyboard.inline_keyboard[-1][-1]
	await call.message.edit_reply_markup(reply_markup=keyboard)

	lang = locales_dict[call.message.chat.id]
	api = TikTokAPI(lang)
	api.link = call.data.split('==')[1]
	await api.check_file_in_db_and_get_data()
	link = f'https://www.tiktok.com/@{api.result["author"]["uniqueId"]}'
	await api.initialize(call.message, link)

	photo = FSInputFile(api.path, api.author)
	await call.message.answer_photo(photo, api.caption)

	await api.delete_file()


@router.callback_query(F.data.startswith('videos'))
async def videos_handler(call: CallbackQuery):
	count = int(call.data[7])
	url = call.data.split("==")[1]

	lang = locales_dict[call.message.chat.id]
	api = TikTokAPI(lang)

	links, tt_chain_token = await api.get_videos(url)