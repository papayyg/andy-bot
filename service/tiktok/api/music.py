import httpx
import aiofiles
from aiogram.types import FSInputFile, BufferedInputFile

from utils.db import tiktok
from locales.translations import _

class Music:
    def __init__(self, data) -> None:
        self.id = data["id"]
        self.file_id = None
        self.thumbnail = None
        self.author = data["authorName"]
        self.title = data["title"]
        self.link = data["playUrl"]
        self.cover = data["coverLarge"]
        self.duration = data["duration"]
        self.stats = None
        
    async def download(self):
        if not await self.check_id():
            self.parent.path = f'temp/{self.parent.unique_id}/audio.mp3'

            cookies = {"tt_chain_token": self.parent.tt_chain_token}
            headers = {"referer": "https://www.tiktok.com/"}
            async with httpx.AsyncClient() as client:
                response = await client.get(self.link, cookies=cookies, headers=headers)
                async with aiofiles.open(self.parent.path, "wb") as f:
                    await f.write(response.content)
                self.file_id = FSInputFile(self.parent.path, self.parent.user.unique_name)

                response = await client.get(self.cover, cookies=cookies, headers=headers)
                self.thumbnail = BufferedInputFile(response.content, 'thumbnail')
        return self.file_id
    
    async def get_caption(self, lang):
        author = f'👤 <a href="{self.parent.link}">{self.author}</a>'
        text = f'{author}\n<i>{await _("00024", lang)}</i>: <b>{self.stats}</b>'
        return text
    
    async def check_id(self):
        r = await tiktok.music_exists(self.id)
        if r:
            self.file_id = r["file_id"]
        return r
    
    async def save(self):
        data = {
            "_id": self.id,
            "file_id": self.file_id,
            "author": self.author,
            "title": self.title,
            "link": self.link,
            "cover": self.cover,
            "duration": self.duration,
        }
        await tiktok.save_music(data)
