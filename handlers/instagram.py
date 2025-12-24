from aiogram import Bot
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from service.instagram.instagram import InstagramAPI
from keyboards.inline import inst_commnet_keyboard
from locales.translations import _
from utils.locales import locales_dict
from config import owner_id

router = Router()

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.contains('instagram.com/'))
async def instagram_message_group(message: Message, bot: Bot):
    lang = locales_dict[message.chat.id]
    user = message.from_user.mention_html()
    try:
        async with InstagramAPI(message) as api:
            if api.type == 'image':
                image = await api.post.download()
                caption = await api.post.create_group_caption(user)
                keyboard = await api.post.crate_group_keyboard()
                api.file_id = (await message.answer_photo(image, caption=caption, reply_markup=keyboard)).photo[-1].file_id

            elif api.type == 'carousel':
                groups = await api.post.download(user)
                api.file_id = []
                for media_group in groups:
                    carousel = await message.answer_media_group(media_group.build())
                    for image in carousel:
                        try:
                            api.file_id.append(['p', image.photo[-1].file_id])
                        except:
                            api.file_id.append(['v', image.video.file_id])

            elif api.type == 'video':
                video, width, height = await api.post.download()
                if not video:
                    return await message.answer(await _("00027", lang))
                caption = await api.post.create_group_caption(user)
                keyboard = await api.post.crate_group_keyboard()
                api.file_id = (await message.answer_video(video, caption=caption, width=width, height=height, reply_markup=keyboard)).video.file_id

            elif api.type == 'profile':
                avatar = await api.user.get_avatar()
                caption = await api.user.create_group_caption(user)
                api.file_id = (await message.answer_photo(avatar, caption=caption)).photo[-1].file_id

            elif api.type in ['stories-image', 'highlights-image']:
                image = await api.stories.download()
                caption = await api.stories.create_group_caption(lang, user)
                api.file_id = (await message.answer_photo(image, caption=caption)).photo[-1].file_id

            elif api.type in ['stories-video', 'highlights-video']:
                video, width, height, duration = await api.stories.download()
                if not video:
                    return await message.answer(await _("00027", lang))
                caption = await api.stories.create_group_caption(lang, user)
                api.file_id = (await message.answer_video(video, caption=caption, width=width, height=height, duration=duration)).video.file_id
            
            elif api.type == 'audio':
                audio, duration = await api.audio.download()
                cover, performer, title = await api.audio.get_cover()
                caption = await api.audio.create_group_caption(user)
                api.file_id = (await message.answer_audio(audio, caption=caption, duration=duration, thumbnail=cover, performer=performer, title=title)).audio.file_id
                
            elif api.type == 'locations':
                caption = await api.locations.create_group_caption(user)
                await message.answer(caption, disable_web_page_preview=True)

            elif api.type == 'tags':
                caption = await api.tags.create_group_caption(lang, user)
                cover = await api.tags.get_cover()
                await message.answer_photo(cover, caption, disable_web_page_preview=True)
                
            await message.delete()
    except Exception as e:
        print(e)
        await message.answer(await _("00038", lang))
        await bot.send_message(owner_id, f'Ошибка: {message.text} {message.chat.id}')

@router.message(F.text.contains('instagram.com/'))
async def instagram_message(message: Message, bot: Bot):
    ff = await message.answer(await _('00006', locales_dict[message.chat.id]))
    lang = locales_dict[message.chat.id]
    try:
        async with InstagramAPI(message) as api:
            if api.type == 'image':
                image = await api.post.download()
                caption = await api.post.create_caption()
                keyboard = await api.post.crate_keyboard()
                api.file_id = (await message.answer_photo(image, caption=caption, reply_markup=keyboard)).photo[-1].file_id
            elif api.type == 'carousel':
                groups = await api.post.download()
                api.file_id = []
                for media_group in groups:
                    carousel = await message.answer_media_group(media_group.build())
                    for image in carousel:
                        try:
                            api.file_id.append(['p', image.photo[-1].file_id])
                        except:
                            api.file_id.append(['v', image.video.file_id])
            elif api.type == 'video':
                video, width, height = await api.post.download()
                if not video:
                    return await message.answer(await _("00027", lang))
                caption = await api.post.create_caption()
                keyboard = await api.post.crate_keyboard()
                api.file_id = (await message.answer_video(video, caption=caption, width=width, height=height, reply_markup=keyboard)).video.file_id

            elif api.type == 'profile':
                avatar = await api.user.get_avatar()
                caption = await api.user.create_caption(lang)
                api.file_id = (await message.answer_photo(avatar, caption=caption)).photo[-1].file_id

            elif api.type in ['stories-image', 'highlights-image']:
                image = await api.stories.download()
                caption = await api.stories.create_caption(lang)
                keyboard = await api.stories.crate_keyboard()
                api.file_id = (await message.answer_photo(image, caption=caption, reply_markup=keyboard)).photo[-1].file_id

            elif api.type in ['stories-video', 'highlights-video']:
                video, width, height, duration = await api.stories.download()
                if not video:
                    return await message.answer(await _("00027", lang))
                caption = await api.stories.create_caption(lang)
                keyboard = await api.stories.crate_keyboard()
                api.file_id = (await message.answer_video(video, caption=caption, width=width, height=height, reply_markup=keyboard, duration=duration)).video.file_id
            
            elif api.type == 'audio':
                audio, duration = await api.audio.download()
                cover, performer, title = await api.audio.get_cover()
                caption = await api.audio.create_caption()
                api.file_id = (await message.answer_audio(audio, caption=caption, duration=duration, thumbnail=cover, performer=performer, title=title)).audio.file_id
                
            elif api.type == 'locations':
                caption = await api.locations.create_caption()
                await message.answer(caption, disable_web_page_preview=True)

            elif api.type == 'tags':
                caption = await api.tags.create_caption(lang)
                cover = await api.tags.get_cover()
                await message.answer_photo(cover, caption, disable_web_page_preview=True)
                
            await message.delete()
        await ff.delete()
    except Exception as e:
        print(e)
        await ff.delete()
        await message.answer(await _("00038", lang))
        await bot.send_message(owner_id, f'Ошибка: {message.text} {message.chat.id}')

@router.callback_query(F.data.startswith('inst_stats'))
async def stats_handler(call: CallbackQuery):
    lang = locales_dict[call.message.chat.id]
    pk = call.data.split('==')[1]
    text = await InstagramAPI.get_stats(pk, lang)
    await call.answer(text, show_alert=True)

@router.callback_query(F.data.startswith('inst_profile'))
async def profile_handler(call: CallbackQuery):   
    lang = locales_dict[call.message.chat.id]
    pk = call.data.split('inst_profile==')[1]
    avatar, caption = await InstagramAPI.get_profile(pk, lang)
    await call.message.answer_photo(avatar, caption=caption)

    keyboard = call.message.reply_markup
    del keyboard.inline_keyboard[0][-1]
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()

@router.callback_query(F.data.startswith('inst_comments'))
async def comments_handler(call: CallbackQuery):
    pk = call.data.split('==')[1]
    text = await InstagramAPI.get_comments(pk, 5)
    
    new_keyboard = await inst_commnet_keyboard(call.message.chat.id, pk)
    await call.message.reply(text, disable_web_page_preview=True, reply_markup=new_keyboard)

    keyboard = call.message.reply_markup
    del keyboard.inline_keyboard[-1]
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()

@router.callback_query(F.data.startswith('inst_more_comments'))
async def more_comments_handler(call: CallbackQuery):
    pk = call.data.split('==')[1]
    text = await InstagramAPI.get_comments(pk, 10)
    await call.message.edit_text(text, disable_web_page_preview=True)
    await call.answer()