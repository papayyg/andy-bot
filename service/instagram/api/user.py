import aiohttp
import httpx
import re
from aiogram.types import BufferedInputFile
from config import INST_SESSION

from locales.translations import _
from utils.locales import locales_dict

class User:
    def __init__(self, data) -> None:
        self.id = data.get("id")
        self.full_name = data.get("full_name")
        self.username = data.get("username")
        self.biography = data.get("biography")
        self.category_name = data.get("category_name") 
        self.avatar = data.get("profile_pic_url")
        self.follower = data["edge_followed_by"].get("count") if 'edge_followed_by' in data else None
        self.following = data["edge_follow"].get("count") if 'edge_follow' in data else None
        self.bio_links = data.get("bio_links")
        
        self.cookies = {
            'sessionid': INST_SESSION,
        }
        self.parent = None

    async def extract_profile_name(self):
        pattern = r'(?:http[s]?://)?(?:www\.)?(?:instagram\.com/)?([a-zA-Z0-9_\.]+)/?'
        match = re.search(pattern, self.parent.link)
        self.username = match.group(1)

    async def get_data(self):
        params = {
            'username': self.username,
        }
        headers = {
            'x-ig-app-id': '936619743392459',
        }
        async with aiohttp.ClientSession() as session:
            response = await session.get('https://www.instagram.com/api/v1/users/web_profile_info/', cookies=self.cookies, params=params, headers=headers)
            data = (await response.json())["data"]["user"]

            self.id = data["id"]
            self.full_name = data["full_name"]
            self.username = data["username"]
            self.biography = data["biography"]
            self.category_name = data["category_name"]
            self.avatar = data["profile_pic_url_hd"]
            self.follower = data["edge_followed_by"]["count"]
            self.following = data["edge_follow"]["count"]
            self.media = data["edge_owner_to_timeline_media"]["count"]
            self.bio_links = data["bio_links"]
            
    async def create_caption(self, lang):
        link = f'➡️ instagram.com/{self.username}/'
        category = f'\nℹ️ {self.category_name}' if self.category_name else ''
        title = f'👤 <b>{self.full_name}</b>{category}\n{link}'
        desc = f'\n\n{self.biography}' if self.biography != '' else ''
        links = ''
        for link in self.bio_links:
            links += f'\n▫️ {link["title"] + " - " if link["title"] else ""}{link["url"]}'

        follower = f'<i>{await _("00007", lang)} - {await self.readable_number(self.follower)}</i>'
        following = f'<i>{await _("00008", lang)} - {await self.readable_number(self.following)}</i>'
        media = f'<i>{await _("00033", lang)} - {await self.readable_number(self.media)}</i>'
        stats = f'\n\n🔎 <u>{await _("00011", lang)}:</u>\n{follower}\n{following}\n{media}'

        text = f'{title}{desc}{links}{stats}'
        return text

    async def create_group_caption(self, user):
        link = f'➡️ instagram.com/{self.username}/'
        category = f'\nℹ️ {self.category_name}' if self.category_name else ''
        title = f'🆔 <b>{self.full_name}</b>{category}\n{link}'
        desc = f'\n\n{self.biography}' if self.biography != '' else ''
        links = ''
        for link in self.bio_links:
            links += f'\n▫️ {link["title"] + " - " if link["title"] else ""}{link["url"]}'

        text = f'👤 {user}\n\n{title}{desc}{links}'
        return text

    async def readable_number(self, number):
        number_str = str(number)
        groups = []
        while number_str:
            groups.append(number_str[-3:])
            number_str = number_str[:-3]
        return ' '.join(reversed(groups))

    async def get_avatar(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.avatar)
            return BufferedInputFile(response.content, self.username)