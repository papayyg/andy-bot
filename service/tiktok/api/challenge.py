import httpx
import aiofiles
from aiogram.types import FSInputFile, BufferedInputFile

from utils.db import tiktok
from locales.translations import _

class Challenge:
    def __init__(self, data) -> None:
        self.id = data["challenge"]["id"]
        self.title = data["challenge"]["title"]
        self.stats = data["statsV2"]
        self.parent = None

    async def create_caption(self, lang):
        stats = f'<i>{await _("00024", lang)}</i>: <b>{await Challenge.readable_number(self.stats["videoCount"])}</b>\n<i>{await _("00025", lang)}</i>: <b>{await Challenge.readable_number(self.stats["viewCount"])}</b>'
        caption = f'#️⃣ <a href="{self.parent.link}">{self.title}</a>\n{stats}\n\n<b><i>{await _("00026", lang)}:</i></b>'
        return caption
        
    async def readable_number(number):
        number_str = str(number)
        groups = []
        while number_str:
            groups.append(number_str[-3:])
            number_str = number_str[:-3]
        return ' '.join(reversed(groups))