import httpx
import aiofiles
from datetime import datetime

from .user import User
from .music import Music

class Video:
    def __init__(self, data) -> None:
        self.id = data["id"]
        self.desc = data["desc"].replace('<', '\\<').replace('>', '\\>')
        self.second_desc = None
        self.create_time = data["createTime"]

        self.height = data["video"]["height"]
        self.width = data["video"]["width"]
        self.duration = data["video"]["duration"]
        self.cover = data["video"]["cover"]
        self.cover_gif = data["video"]["dynamicCover"]

        self.download_link = data["video"]["playAddr"]
        self.watermark_link = data["video"]["downloadAddr"]

        self.parent = None

    async def set_time(self):
        dt = datetime.fromtimestamp(int(self.create_time))
        self.create_time = dt.strftime("%H:%M - %d.%m.%y")

    async def download(self, link):
        self.parent.path += '/video.mp4'

        cookies = {'tt_chain_token': self.parent.tt_chain_token}
        headers = {'referer': 'https://www.tiktok.com/'}
        async with httpx.AsyncClient() as client:
            response = await client.get(link, cookies=cookies, headers=headers)
            async with aiofiles.open(self.parent.path, 'wb') as f:
                await f.write(response.content)
    
    async def create_caption(self):
        await self.set_time()
        
        if self.desc != '':
            self.desc = f'📝 {self.desc}'
        if len(self.desc) > 870:
            self.second_desc = self.desc[870:]
            self.desc = self.desc[:870] 

        return f'👤 <a href="{self.parent.link}">{self.parent.author.unique_name}</a>\n\n{self.desc}'