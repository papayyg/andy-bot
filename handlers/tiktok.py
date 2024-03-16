import re

from aiogram import Router, F
from aiogram.types import Message, FSInputFile, CallbackQuery

from service import tiktok
from keyboards.inline import tiktok_video_options
from locales.translations import _
from utils.locales import locales_dict
from utils.db.files import save_file, file_exists, add_watermark

router = Router()

@router.message(F.text.contains('tiktok.com/'))
async def tiktok_message(message: Message):
	tiktok_link = await tiktok.extract_tiktok_link(message.text)

	db = await file_exists(tiktok_link)
	if not db:
		data_type, result, tt_chain_token = await tiktok.get_data(tiktok_link)
	else:
		data_type, result, video = db["data_type"], db["result"], db["file_id"]

	if data_type == 'video':
		link = result["video"]["playAddr"]
		author = result["author"]["uniqueId"].replace('<', '\\<').replace('>', '\\>')
		duration = result["video"]["duration"]
		width = result["video"]["width"]
		height = result["video"]["height"]
		descr = result["desc"].replace('<', '\\<').replace('>', '\\>')
		descr = descr[:870]
		descr_second = descr[870:] if len(descr) > 870 else ''
		
		caption = f'👤 <a href="{tiktok_link}">{author}</a>\n\n📝 {descr}'
		keyboard = await tiktok_video_options(message.chat.id, result["video"]["cover"], result["video"]["dynamicCover"], tiktok_link)

		if not db:
			path = f'temp/tiktok_{message.chat.id + message.message_id}.mp4'
			await tiktok.get_video(link, tt_chain_token, path)
			video = FSInputFile(path, author)
		
		
		answer = await message.answer_video(video, duration, width, height, caption=caption, reply_markup=keyboard)
		if not db: await save_file(tiktok_link, answer.video.file_id, data_type, result)

		if descr_second: await message.answer(descr_second)
		await message.delete()
		await tiktok.delete_video(path)


@router.callback_query(F.data.startswith('watermark'))
async def register_chat(call: CallbackQuery):
	await call.answer(await _('00006', locales_dict[call.message.chat.id]))
	keyboard = call.message.reply_markup
	keyboard.inline_keyboard.pop()
	await call.message.edit_reply_markup(reply_markup=keyboard)

	tiktok_link = call.data.split('==')[1]
	db = await file_exists(tiktok_link)
	if "watermark" not in db:
		data_type, result, tt_chain_token = await tiktok.get_data(tiktok_link)
	else:
		data_type, result, video = db["data_type"], db["result"], db["file_id"]
	link = result["video"]["downloadAddr"]

	author = result["author"]["uniqueId"].replace('<', '\\<').replace('>', '\\>')
	duration = result["video"]["duration"]
	width = result["video"]["width"]
	height = result["video"]["height"]

	if "watermark" not in db:
		path = f'temp/tiktok_{call.message.chat.id + call.message.message_id}.mp4'
		await tiktok.get_video(link, tt_chain_token, path)
		video = FSInputFile(path, author)

	answer = await call.message.answer_video(video, duration, width, height)
	if "watermark" not in db: await add_watermark(tiktok_link, answer.video.file_id)
	await tiktok.delete_video(path)
