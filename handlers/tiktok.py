import shutil
from aiogram import Bot
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from service.tiktok.tiktok import TikTokAPI
from keyboards.inline import commnet_keyboard
from locales.translations import _
from utils.locales import locales_dict
from config import owner_id

router = Router()

async def get_audio(api, message, keyboard=None):
    audio = await api.music.download()
    r = await message.answer_audio(audio, duration=api.music.duration, performer=api.music.author, title=api.music.title, thumbnail=api.music.thumbnail, reply_markup=keyboard)
    api.music.file_id = r.audio.file_id
    await api.music.save()
    
@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.contains('tiktok.com/'))
async def tiktok_message_group(message: Message, bot: Bot):
    lang = locales_dict[message.chat.id]
    new_video = None
    user = message.from_user.mention_html()
    try:
        async with TikTokAPI(message) as api:
            if api.type == 'video':
                video = await api.video.download(api.video.download_link)
                if video == False:
                    return await message.answer(await _("00027", lang))
                caption = await api.video.create_caption_for_group(user)
                keyboard = await api.video.crate_keyboard_for_group()
                new_video = await message.answer_video(video, api.video.duration, api.video.width, api.video.height, caption=caption)
                api.video.file_id = new_video.video.file_id
                await api.video.save()

            elif api.type == 'profile':
                photo = await api.user.download_cover()
                caption = await api.user.create_caption_for_group(user)
                await message.answer_photo(photo, caption=caption)
            
            elif api.type == 'slides':
                groups = await api.slides.get_slides(user)
                keyboard = await api.slides.crate_keyboard_for_group()
                for media_group in groups:
                    photos = await message.answer_media_group(media_group.build())
                    for photo in photos:
                        api.slides.files_ids.append(photo.photo[-1].file_id)
                await api.slides.save()

                await get_audio(api, message, keyboard)
                
            elif api.type == 'music':
                photo = await api.user.download_cover()
                caption = await api.music.create_caption_for_group(lang, user)
                await message.answer_photo(photo, caption=caption, disable_web_page_preview=True)
                await get_audio(api, message)

            elif api.type == "challenge":
                caption = await api.challenge.create_caption_for_group(lang, user)
                text = await message.answer(caption, disable_web_page_preview=True)
                video = await api.video.download(api.video.download_link)
                caption = await api.video.create_caption_for_group(user)
                keyboard = None
                new_video = await text.reply_video(video, api.video.duration, api.video.width, api.video.height, caption=caption)
                api.video.file_id = new_video.video.file_id 
                await api.video.save()
                
            elif api.type == "stories":
                video, caption = await api.ssstik_download(user)
                await message.answer_video(video, caption=caption)

            elif api.type == "live":
                return

            elif api.type == "playlist":
                return
                
            await message.delete()
        
        if new_video and keyboard:
            await new_video.edit_reply_markup(reply_markup=keyboard)
    except:
        await message.answer(await _("00038", lang))
        await bot.send_message(owner_id, f'Ошибка: {message.text} {message.chat.id}')

@router.message(F.text.contains('tiktok.com/'))
async def tiktok_message(message: Message, bot: Bot):
    ff = await message.answer(await _('00006', locales_dict[message.chat.id]))
    lang = locales_dict[message.chat.id]
    new_video = None
    try:
        async with TikTokAPI(message) as api:
            if api.type == 'video':
                video = await api.video.download(api.video.download_link)
                if video == False:
                    return await message.answer(await _("00027", lang))
                caption = await api.video.create_caption()
                keyboard = await api.video.crate_keyboard()
                new_video = await message.answer_video(video, api.video.duration, api.video.width, api.video.height, caption=caption)
                if api.video.second_desc: await message.answer(api.video.second_desc)
                api.video.file_id = new_video.video.file_id
                await api.video.save()

                await get_audio(api, message)

            elif api.type == 'profile':
                photo = await api.user.download_cover()
                caption = await api.user.create_caption(lang)
                await message.answer_photo(photo, caption=caption)
            
            elif api.type == 'slides':
                groups = await api.slides.get_slides()
                keyboard = await api.slides.crate_keyboard()
                for media_group in groups:
                    photos = await message.answer_media_group(media_group.build())
                    for photo in photos:
                        api.slides.files_ids.append(photo.photo[-1].file_id)
                await api.slides.save()

                await get_audio(api, message, keyboard)
                
            elif api.type == 'music':
                photo = await api.user.download_cover()
                caption = await api.music.create_caption(lang)
                await message.answer_photo(photo, caption=caption, disable_web_page_preview=True)
                await get_audio(api, message)

            elif api.type == "challenge":
                caption = await api.challenge.create_caption(lang)
                text = await message.answer(caption, disable_web_page_preview=True)
                video = await api.video.download(api.video.download_link)
                caption = await api.video.create_caption()
                keyboard = None
                new_video = await text.reply_video(video, api.video.duration, api.video.width, api.video.height, caption=caption)
                api.video.file_id = new_video.video.file_id 
                await api.video.save()
                
            elif api.type == "stories":
                video, caption = await api.ssstik_download()
                await message.answer_video(video, caption=caption)

            elif api.type == "live":
                await ff.delete()
                return await message.answer(await _("00028", lang))

            elif api.type == "playlist":
                await ff.delete()
                return await message.answer(await _("00029", lang))
                
                
            await message.delete()
        
        if new_video and keyboard:
            await new_video.edit_reply_markup(reply_markup=keyboard)
        await ff.delete()
    except:
        await ff.delete()
        await message.answer(await _("00038", lang))
        await bot.send_message(owner_id, f'Ошибка: {message.text} {message.chat.id}')

@router.callback_query(F.data.startswith('watermark'))
async def watermark_handler(call: CallbackQuery):
    id = call.data.split("==")[1]
    video, api = await TikTokAPI.video.get_watermark_video(id)
    r = await call.message.answer_video(video, api["duration"], api["width"], api["height"])
    await TikTokAPI.video.save_watermark_id(id, r.video.file_id)

    keyboard = call.message.reply_markup
    del keyboard.inline_keyboard[1]
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()

@router.callback_query(F.data.startswith('stats'))
async def stats_handler(call: CallbackQuery):
    lang = locales_dict[call.message.chat.id]
    id = call.data.split('==')[1]
    text = await TikTokAPI.video.get_stats(id, lang)
    await call.answer(text, show_alert=True)

@router.callback_query(F.data.startswith('slide_stats'))
async def slide_stats_handler(call: CallbackQuery):
    lang = locales_dict[call.message.chat.id]
    id = call.data.split('==')[1]
    text = await TikTokAPI.slides.get_stats(id, lang)
    await call.answer(text, show_alert=True)

@router.callback_query(F.data.startswith('makevideo'))
async def makevideo_handler(call: CallbackQuery, bot: Bot):
    lang = locales_dict[call.message.chat.id]
    await call.answer(await _("00006", lang), show_alert=False)
    
    keyboard = call.message.reply_markup
    del keyboard.inline_keyboard[0]
    await call.message.edit_reply_markup(reply_markup=keyboard)
    
    id = call.data.split('==')[1]
    video, duration, unique_id, width, height = await TikTokAPI.slides.create_video(id, bot)
    if duration:
        sended_video = await call.message.answer_video(video, duration=duration, height=height, width=width)
        await TikTokAPI.slides.save_slides_show_id(id, sended_video.video.file_id)
        try:
            shutil.rmtree(f'temp/{unique_id}')
        except:
            pass
    else:
        await call.message.answer_video(video)
    
@router.callback_query(F.data.startswith('profile'))
async def profile_handler(call: CallbackQuery):   
    tt_chain_token = call.data.split('profile==')[1]
    photo, text = await TikTokAPI.user.get_profile(tt_chain_token)
    await call.message.answer_photo(photo, caption=text)

    keyboard = call.message.reply_markup
    del keyboard.inline_keyboard[-2][-1]
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()
    
@router.callback_query(F.data.startswith('comments'))
async def comments_handler(call: CallbackQuery):
    lang = locales_dict[call.message.chat.id]
    id = call.data.split('==')[1]
    text = await TikTokAPI.video.get_comments(id, 5)
    
    if text:
        new_keyboard = await commnet_keyboard(call.message.chat.id, id)
        await call.message.reply(text, disable_web_page_preview=True, reply_markup=new_keyboard)
    else:
        await call.answer(await _("00034", lang))

    keyboard = call.message.reply_markup
    del keyboard.inline_keyboard[-1]
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()

@router.callback_query(F.data.startswith('more_comments'))
async def more_comments_handler(call: CallbackQuery):
    id = call.data.split('==')[1]
    text = await TikTokAPI.video.get_comments(id, 10)
    await call.message.edit_text(text, disable_web_page_preview=True)
    await call.answer()
