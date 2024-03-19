import httpx
import aiofiles
from datetime import datetime
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup

from .user import User
from .music import Music
from utils.db import tiktok
from locales.translations import _
from utils.locales import locales_dict



class Video:
    def __init__(self, data) -> None:
        self.id = data["id"]
        self.file_id = None
        self.watermark_id = None
        self.desc = data["desc"].replace("<", "\\<").replace(">", "\\>")
        self.second_desc = None
        self.create_time = data["createTime"]

        self.height = data["video"]["height"]
        self.width = data["video"]["width"]
        self.duration = data["video"]["duration"]
        self.cover = data["video"]["cover"]
        self.cover_gif = data["video"]["dynamicCover"]

        self.download_link = data["video"]["playAddr"]
        self.watermark_link = data["video"]["downloadAddr"]

        self.stats = {
            "likes": data["statsV2"]["diggCount"],
            "share": data["statsV2"]["shareCount"],
            "comment": data["statsV2"]["commentCount"],
            "play": data["statsV2"]["playCount"],
            "collect": data["statsV2"]["collectCount"],
        }

        self.parent = None

    async def set_time(self):
        dt = datetime.fromtimestamp(int(self.create_time))
        self.create_time = dt.strftime("%H:%M - %d.%m.%y")

    async def check_id(self):
        r = await tiktok.id_exists(self.id)
        if r:
            self.file_id = r["file_id"]
        return r
        
    async def download(self, link):
        if not await self.check_id():
            self.parent.path += "/video.mp4"

            cookies = {"tt_chain_token": self.parent.tt_chain_token}
            headers = {"referer": "https://www.tiktok.com/"}
            async with httpx.AsyncClient() as client:
                response = await client.get(link, cookies=cookies, headers=headers)
                async with aiofiles.open(self.parent.path, "wb") as f:
                    await f.write(response.content)
            self.file_id = FSInputFile(self.parent.path, self.parent.author.unique_name)
        return self.file_id

    async def create_caption(self):
        await self.set_time()

        if self.desc != "":
            self.desc = f"📝 {self.desc}"
        if len(self.desc) > 870:
            self.second_desc = self.desc[870:]
            self.desc = self.desc[:870]

        return f'👤 <a href="{self.parent.link}">{self.parent.author.unique_name}</a>\n\n{self.desc}'
    
    async def crate_keyboard(self):
        lang = locales_dict[self.parent.message.chat.id]
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=await _("00003", lang), url=self.cover),
                    InlineKeyboardButton(text=await _("00004", lang), url=self.cover_gif),
                ],
                [InlineKeyboardButton(text=await _("00005", lang), callback_data=f"watermark=={self.id}")],
                [
                    InlineKeyboardButton(text=await _("00013", lang), callback_data=f"stats=={self.id}"),
                    InlineKeyboardButton(text=await _("00012", lang), callback_data=f"profile=={self.id}")
                ]
            ]
        )
        return keyboard

    async def save(self):
        data = {
            "_id": self.id,
            "file_id": self.file_id,
            "watermark_file_id": self.watermark_id,
            "desc": self.desc,
            "second_desc": self.second_desc,
            "create_time": self.create_time,
            "height": self.height,
            "width": self.width,
            "duration": self.duration,
            "cover": self.cover,
            "cover_gif": self.cover_gif,
            "download_link": self.download_link,
            "watermark_link": self.watermark_link,
            "stats": self.stats
        }
        await tiktok.save_video(data)
