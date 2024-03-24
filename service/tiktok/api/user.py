import httpx
import aiofiles
from aiogram.types import FSInputFile, BufferedInputFile

from utils.db import tiktok
from locales.translations import _

class User:
    def __init__(self, data) -> None:
        self.id = data["id"]
        self.file_id = None
        self.unique_name = data["uniqueId"].replace('<', '\\<').replace('>', '\\>')
        self.name = data["nickname"]

        self.avatar = data["avatarLarger"]
        self.signature = data["signature"].replace('<', '\\<').replace('>', '\\>')

        self.parent = None
        self.stats = None
        self.bio_links = None

    async def download_cover(self):
        self.parent.path += "/cover.jpg"

        cookies = {"tt_chain_token": self.parent.tt_chain_token}
        headers = {"referer": "https://www.tiktok.com/"}
        async with httpx.AsyncClient() as client:
            response = await client.get(self.avatar, cookies=cookies, headers=headers)
            async with aiofiles.open(self.parent.path, "wb") as f:
                await f.write(response.content)
            self.file_id = FSInputFile(self.parent.path, self.unique_name)
        return self.file_id
    
    async def create_caption(self, lang):
        link = f'➡️ tiktok.com/@{self.unique_name}'
        titke = f'👤 <b>{self.name}</b>\n{link}'
        desc = f'\n\n{self.signature}' if self.signature != '' else ''
        bio_link = f'\n\n🔗 {self.bio_links}' if self.bio_links else ''
        
        follower = f'<i>{await _("00007", lang)} - {await User.readable_number(self.stats["followerCount"])}</i>'
        following = f'<i>{await _("00008", lang)} - {await User.readable_number(self.stats["followingCount"])}</i>'
        heart = f'<i>{await _("00009", lang)} - {await User.readable_number(self.stats["heartCount"])}</i>'
        video = f'<i>{await _("00010", lang)} - {await User.readable_number(self.stats["videoCount"])}</i>'
        stats = f'\n\n🔎 <u>{await _("00011", lang)}:</u>\n{follower}\n{following}\n{heart}\n{video}'

        return f'{titke}{desc}{bio_link}{stats}'

    async def readable_number(number):
        number_str = str(number)
        groups = []
        while number_str:
            groups.append(number_str[-3:])
            number_str = number_str[:-3]
        return ' '.join(reversed(groups))
    
    async def get_profile(tt_chain_token):
        link = await tiktok.get_data_by_token(tt_chain_token)
        if 'author' in link["data"]:
            author = link["data"]["author"]
        else:
            author = link["data"]["itemInfo"]["itemStruct"]["author"]
        cookies = {"tt_chain_token": link["tt_chain_token"]}
        headers = {"referer": "https://www.tiktok.com/"}

        link = f'➡️ tiktok.com/@{author["uniqueId"]}'
        title = f'👤 <b>{author["nickname"]}</b>\n{link}'
        desc = f'\n\n{author["signature"]}' if author["signature"] != '' else ''
        text = f'{title}{desc}'

        async with httpx.AsyncClient() as client:
            response = await client.get(author["avatarLarger"], cookies=cookies, headers=headers)
            return BufferedInputFile(response.content, author["uniqueId"]), text
            