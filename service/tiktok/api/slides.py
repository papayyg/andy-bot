import httpx
import aiofiles
import os
import uuid
import asyncio
from datetime import datetime
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import FSInputFile
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
import moviepy.video.fx.all as vfx

from utils.db import tiktok
from locales.translations import _
from utils.locales import locales_dict

class Slides:
    def __init__(self, data) -> None:
        self.id = data["id"]
        self.desc = data["desc"]
        self.second_desc = None
        self.create_time = data["createTime"]
        self.stats = data["statsV2"]
        self.images = []
        for image in data["imagePost"]["images"]:
            self.images.append(image["imageURL"]["urlList"][0])
        self.files_ids = []
        self.parent = None

    async def create_caption(self):
        await self.set_time()

        if self.desc != "":
            self.desc = f"📝 {self.desc}"
        if len(self.desc) > 870:
            self.second_desc = self.desc[870:]
            self.desc = self.desc[:870]

        return f'👤 <a href="{self.parent.link}">{self.parent.user.unique_name}</a>\n\n{self.desc}'

    async def check_slides_id(self):
        r = await tiktok.slides_exists(self.id)
        if r:
            self.files_ids = r["files_ids"]
        return r
            
    async def get_slides(self):
        groups = []
        caption = await self.create_caption()
        media_group = MediaGroupBuilder(caption=caption)
        i = 0
        if not await self.check_slides_id():
            async with httpx.AsyncClient() as client:
                cookies = {"tt_chain_token": self.parent.tt_chain_token}
                headers = {"referer": "https://www.tiktok.com/"}
                for slide in self.images:
                    new_path = f'{self.parent.path}/{i}.jpg'
                    response = await client.get(slide, cookies=cookies, headers=headers, follow_redirects=True)
                    async with aiofiles.open(new_path, "wb") as f:
                        await f.write(response.content)
                    photo = FSInputFile(new_path, str(i))
                    media_group.add_photo(photo)
                    i += 1

                    if i % 10 == 0 and not (len(self.images) % 10 == 0 and slide == self.images[-1]):
                        media_group.caption = None
                        groups.append(media_group)
                        media_group = MediaGroupBuilder(caption=caption)
        else:
            for slide in self.files_ids:
                media_group.add_photo(slide)
                i += 1
                if i % 10 == 0:
                    media_group.caption = None
                    groups.append(media_group)
                    media_group = MediaGroupBuilder(caption=caption)

        groups.append(media_group)
        return groups
    
    async def get_stats(id, lang):
        result = await tiktok.slides_exists(id)
        stats = result["stats"]
        text = f'{result["create_time"]}\n\n'
        text += f'❤️ {await _("00014", lang)} - {await Slides.readable_number(stats["diggCount"])}\n'
        text += f'💬 {await _("00015", lang)} - {await Slides.readable_number(stats["commentCount"])}\n'
        text += f'📣 {await _("00016", lang)} - {await Slides.readable_number(stats["shareCount"])}\n'
        text += f'▶️ {await _("00017", lang)} - {await Slides.readable_number(stats["playCount"])}\n'
        text += f'🌟 {await _("00018", lang)} - {await Slides.readable_number(stats["collectCount"])}\n'
        return text
    
    async def readable_number(number):
        number_str = str(number)
        groups = []
        while number_str:
            groups.append(number_str[-3:])
            number_str = number_str[:-3]
        return ' '.join(reversed(groups))
    
    async def crate_keyboard(self):
        lang = locales_dict[self.parent.message.chat.id]
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=await _("00023", lang), callback_data=f"makevideo=={self.id}")],
                [
                    InlineKeyboardButton(text=await _("00013", lang), callback_data=f"slide_stats=={self.id}"),
                    InlineKeyboardButton(text=await _("00012", lang), callback_data=f"profile=={self.parent.tt_chain_token}")
                ],
                [InlineKeyboardButton(text=await _("00021", lang), callback_data=f"comments=={self.id}")]
            ]
        )
        return keyboard
    
    async def set_time(self):
        dt = datetime.fromtimestamp(int(self.create_time))
        self.create_time = dt.strftime("%H:%M - %d.%m.%y")

    def write_video(final_clip, unique_id):
        final_clip.write_videofile(f'temp/{unique_id}/video.mp4', fps=24, threads=6, codec='libx264', audio_codec='aac', logger=None, temp_audiofile=f'{unique_id}.mp4')

    async def create_video(id, bot):
        slides = await tiktok.slides_exists(id)
        if not slides["video_id"]:
            unique_id = uuid.uuid4().hex
            os.makedirs(f'temp/{unique_id}')
            
            music = await tiktok.music_exists(slides["music_id"])
            file_path = (await bot.get_file(music["file_id"])).file_path
            await bot.download_file(file_path, F'temp/{unique_id}/audio.mp3')

            i = 0
            for image in slides["files_ids"]:
                file_path = (await bot.get_file(image)).file_path
                await bot.download_file(file_path, F'temp/{unique_id}/{i}.jpg')
                i += 1
            files = [os.path.join(f'temp/{unique_id}/', f) for f in os.listdir(f'temp/{unique_id}/') if f.endswith('.jpg')]

            clips = [ImageClip(m).set_duration(2) for m in files]
            video_clips = []
            for i in clips:
                video_clips.extend([i.fx(vfx.fadein, 0.5), i.fx(vfx.fadeout, 0.5)])

            final_clip = concatenate_videoclips(video_clips, method='compose')
            if final_clip.w % 2 != 0:
                final_clip = final_clip.resize(width=final_clip.w + 1)
            if final_clip.h % 2 != 0:
                final_clip = final_clip.resize(height=final_clip.h + 1)

            final_duration = final_clip.duration

            audio = AudioFileClip(f"temp/{unique_id}/audio.mp3")
            while audio.duration < final_duration:
                audio = concatenate_audioclips([audio, audio])
            audio = audio.subclip(0, final_duration)
            final_clip = final_clip.set_audio(audio)

            # final_clip.write_videofile(f'temp/{unique_id}/video.mp4', fps=24, threads=6, codec='libx264', audio_codec='aac', logger= None)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, Slides.write_video, final_clip, unique_id)
            video = FSInputFile(f'temp/{unique_id}/video.mp4', music["author"])
            return video, final_duration, unique_id, final_clip.w, final_clip.h
        else:
            video = slides["video_id"]
            return video, None, None, None, None
        
    
    async def save_slides_show_id(id, file_id):
        await tiktok.save_slides_show_id(id, file_id)
    
    async def save(self):
        data = {
            "_id": self.id,
            "music_id": self.parent.music.id,
            "video_id": None,
            "desc": self.desc,
            "second_desc": self.second_desc,
            "stats": self.stats,
            "create_time": self.create_time,
            "images": self.images,
            "files_ids": self.files_ids
        }
        await tiktok.save_slides(data)