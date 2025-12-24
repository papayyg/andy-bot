import httpx
import aiohttp
import aiofiles
import json
from datetime import datetime
from bs4 import BeautifulSoup
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, BufferedInputFile
from aiogram.utils.media_group import MediaGroupBuilder

from .user import User
from locales.translations import _
from utils.locales import locales_dict

class Post:
    def __init__(self, link) -> None:
        self.pk = None
        self.link = link
        self.parent = None
        self.desc = None
        self.second_desc = None

    async def get_data(self, data):
        if not data:
            async with aiohttp.ClientSession() as client:
                response = await client.get(self.link, cookies=self.parent.cookies, headers=self.parent.headers)
                soup = BeautifulSoup(await response.text(), "html.parser")
                script_tags = soup.find_all('script')
                target_script = None
                is_reels = False
                
                # Сначала ищем новую структуру для reels
                for script_tag in script_tags:
                    if 'xdt_api__v1__clips__home__connection_v2' in str(script_tag):
                        target_script = script_tag.string
                        is_reels = True
                        break
                
                # Если не найдена новая структура, ищем старую
                if not target_script:
                    for script_tag in script_tags:
                        if 'xdt_api__v1__media__shortcode__web_info' in str(script_tag):
                            target_script = script_tag.string
                            break
                
                if is_reels:
                    # Новая структура для reels
                    self.parent.data = json.loads(target_script)["require"][0][3][0]["__bbox"]["require"][0][3][1]["__bbox"]["result"]["data"]["xdt_api__v1__clips__home__connection_v2"]["edges"][0]["node"]["media"]
                else:
                    # Старая структура для фото и других постов
                    self.parent.data = json.loads(target_script)["require"][0][3][0]["__bbox"]["require"][0][3][1]["__bbox"]["result"]["data"]["xdt_api__v1__media__shortcode__web_info"]["items"][0]
            
            await self.set_time()
            
        # Определяем ключ для пользователя (в новой структуре "user", в старой "owner")
        user_key = "user" if "user" in self.parent.data else "owner"
        self.parent.user = User(self.parent.data[user_key])
        self.desc = self.parent.data["caption"]["text"] if self.parent.data.get("caption") else ''
        self.pk = self.parent.data["pk"]
        if self.parent.data.get('carousel_media'):
            self.parent.type = 'carousel'
        elif self.parent.data.get("video_versions"):
            self.parent.type = 'video'
        else:
            self.parent.type = 'image'

    async def crate_keyboard(self):
        lang = locales_dict[self.parent.message.chat.id]
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=await _("00013", lang), callback_data=f"inst_stats=={self.pk}"),
                    InlineKeyboardButton(text=await _("00012", lang), callback_data=f"inst_profile=={self.pk}")
                ],
                [InlineKeyboardButton(text=await _("00021", lang), callback_data=f"inst_comments=={self.pk}")]
            ]
        )
        return keyboard

    async def crate_group_keyboard(self):
        lang = locales_dict[self.parent.message.chat.id]
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=await _("00021", lang), callback_data=f"inst_comments=={self.pk}")]
            ]
        )
        return keyboard
    
    async def set_time(self):
        dt = datetime.fromtimestamp(int(self.parent.data["taken_at"]))
        self.parent.data["taken_at"] = dt.strftime("%H:%M - %d.%m.%y")

    async def create_caption(self):
        if self.desc != "":
            self.desc = f"📝 {self.desc}"
        if len(self.desc) > 870:
            self.second_desc = self.desc[870:]
            self.desc = self.desc[:870]

        return f'👤 <a href="{self.parent.link}">{self.parent.user.username}</a>\n\n{self.desc}'
    
    async def create_group_caption(self, user):
        return f'👤 {user}\n\n🔗 <a href="{self.parent.link}">{self.parent.user.username}</a>'

    async def download(self, user = None):
        async with httpx.AsyncClient() as client:
            if self.parent.type == 'image':
                if not self.parent.file_id:
                    self.parent.path += "/image.jpg"
                    image_link = self.parent.data["image_versions2"]["candidates"][0]["url"]
                
                    response = await client.get(image_link, cookies=self.parent.cookies)
                    async with aiofiles.open(self.parent.path, "wb") as f:
                        await f.write(response.content)
                    self.input_file = FSInputFile(self.parent.path, self.parent.user.username)
                    return self.input_file
                else:
                    return self.parent.file_id
            elif self.parent.type == 'carousel':
                groups = []
                if user:
                    caption = await self.create_group_caption(user)
                else:
                    caption = await self.create_caption()
                media_group = MediaGroupBuilder(caption=caption)
                i = 0
                if not self.parent.file_id:
                    carousel = self.parent.data["carousel_media"]
                    for image in carousel:
                        if not image["video_versions"]:
                            new_path = f'{self.parent.path}/{i}.jpg'
                            response = await client.get(image["image_versions2"]["candidates"][0]["url"])
                            async with aiofiles.open(new_path, "wb") as f:
                                await f.write(response.content)
                            photo = FSInputFile(new_path, str(i))
                            media_group.add_photo(photo)
                            i += 1
                        else:
                            new_path = f'{self.parent.path}/{i}.mp4'
                            response = await client.get(image["video_versions"][0]["url"])
                            async with aiofiles.open(new_path, "wb") as f:
                                await f.write(response.content)
                            video = FSInputFile(new_path, str(i))
                            media_group.add_video(video, width=image["video_versions"][0]["width"], height=image["video_versions"][0]["height"])
                            i += 1

                        if i % 10 == 0 and not (len(carousel) % 10 == 0 and image == carousel[-1]):
                            media_group.caption = None
                            groups.append(media_group)
                            media_group = MediaGroupBuilder(caption=caption)
                else:
                    for arr in self.parent.file_id:
                        media_type = 'photo' if arr[0] == 'p' else 'video'
                        media_group.add(type=media_type, media=arr[1])
                        i += 1
                        if i % 10 == 0:
                            media_group.caption = None
                            groups.append(media_group)
                            media_group = MediaGroupBuilder(caption=caption)

                groups.append(media_group)
                return groups
            
            else:
                data = self.parent.data["video_versions"][0]
                width = data["width"]
                # В новой структуре (reels) используется original_height, в старой - height из video_versions
                height = self.parent.data.get("original_height") or data.get("height")
                if not self.parent.file_id:
                    self.parent.path += "/video.mp4"
                    video_link = data["url"]
                    response = await client.get(video_link, cookies=self.parent.cookies)
                    size = int(response.headers.get("Content-Length", 0))
                    if size > 48000000:
                        return False, width ,height
                    async with aiofiles.open(self.parent.path, "wb") as f:
                        await f.write(response.content)
                    self.input_file = FSInputFile(self.parent.path, self.parent.user.username)
                    return self.input_file, width, height
                else:
                    return self.parent.file_id, width, height
            