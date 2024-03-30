import httpx
import aiohttp
import aiofiles
import json
from datetime import datetime
from bs4 import BeautifulSoup
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup

from .user import User
from locales.translations import _
from utils.locales import locales_dict


headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'sec-fetch-site': 'none',
}

class Stories:
    def __init__(self, link) -> None:
        self.pk = None
        self.link = link
        self.parent = None
        self.title = None
        
        self.headers = headers

    async def get_data(self, data):
        if not data:
            async with aiohttp.ClientSession() as session:
                response = await session.get(self.link, cookies=self.parent.cookies, headers=self.headers, allow_redirects=True)
                soup = BeautifulSoup(await response.text(), "html.parser")
                script_tags = soup.find_all('script')
                target_script = None
                for script_tag in script_tags:
                    if 'xdt_api__v1__feed__reels_media__connection' in str(script_tag):
                        target_script = script_tag.string
                        self.parent.type = 'highlights'
                        break
                    elif 'xdt_api__v1__feed__reels_media' in str(script_tag):
                        target_script = script_tag.string
                        self.parent.type = 'stories'
                        break
            temp_data = json.loads(target_script)["require"][0][3][0]["__bbox"]["require"][0][3][1]["__bbox"]["result"]["data"]
            if self.parent.type == 'stories':
                self.parent.data = temp_data["xdt_api__v1__feed__reels_media"]["reels_media"][0]
            elif self.parent.type == 'highlights':
                self.parent.data = temp_data["xdt_api__v1__feed__reels_media__connection"]["edges"][0]["node"]
        else:
            if 'highlight' in self.parent.data["id"]:
                self.parent.type = 'highlights'
            else:
                self.parent.type = 'stories'
        self.parent.user = User(self.parent.data["user"])
        if 'highlights' in self.parent.type:
            if hasattr(self.parent, 'pk') and self.parent.pk:
                for story in self.parent.data["items"]:
                    if story["pk"] == self.parent.pk:
                        self.parent.temp = story
                        break
            else:
                self.parent.temp = self.parent.data["items"][0]
                self.title = self.parent.data["title"]
        elif 'stories' in self.parent.type:
            for story in self.parent.data["items"]:
                if story["pk"] in self.parent.link:
                    self.parent.temp = story
                    break
        self.parent.data["pk"] = self.parent.temp["pk"]
        if not data: await self.set_time()
        self.pk = self.parent.temp["pk"]
        if self.parent.temp['video_versions']:
            self.parent.type += '-video'
        else:
            self.parent.type += '-image'

    async def crate_keyboard(self):
        lang = locales_dict[self.parent.message.chat.id]
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=await _("00012", lang), callback_data=f"inst_profile=={self.pk}")
                ]
            ]
        )
        return keyboard
    
    async def set_time(self):
        dt = datetime.fromtimestamp(int(self.parent.temp["taken_at"]))
        self.parent.temp["taken_at"] = dt.strftime("%H:%M - %d.%m.%y")

    async def create_caption(self, lang):
        return f'👤 <a href="{self.parent.main_link}">{self.parent.user.username}</a>\n<b>{self.title if self.title else ""}</b>\n🕣 {await _("00035", lang)}: <b><i>{self.parent.temp["taken_at"]}</i></b>'

    async def download(self):
        async with httpx.AsyncClient() as client:
            if 'image' in self.parent.type:
                if not self.parent.file_id:
                    self.parent.path += "/image.jpg"
                    image_link = self.parent.temp["image_versions2"]["candidates"][0]["url"]
                
                    response = await client.get(image_link, cookies=self.parent.cookies)
                    async with aiofiles.open(self.parent.path, "wb") as f:
                        await f.write(response.content)
                    self.input_file = FSInputFile(self.parent.path, self.parent.user.username)
                    return self.input_file
                else:
                    return self.parent.file_id
            
            else:
                data = self.parent.temp["video_versions"][0]
                width = self.parent.temp["original_width"]
                height = self.parent.temp["original_height"]
                duration = int(self.parent.temp["video_duration"])
                if not self.parent.file_id:
                    self.parent.path += "/video.mp4"
                    video_link = data["url"]
                    response = await client.get(video_link, cookies=self.parent.cookies)
                    size = int(response.headers.get("Content-Length", 0))
                    if size > 48000000:
                        return False, width, height, duration
                    async with aiofiles.open(self.parent.path, "wb") as f:
                        await f.write(response.content)
                    self.input_file = FSInputFile(self.parent.path, self.parent.user.username)
                    return self.input_file, width, height, duration
                else:
                    return self.parent.file_id, width, height, duration
            