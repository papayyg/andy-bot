import httpx
import aiohttp
import re
from aiogram.types import BufferedInputFile

from locales.translations import _

class Tags:
    def __init__(self, link) -> None:
        self.pk = None
        self.tag = self.extract_tag(link)
        self.link = link
        self.parent = None
        self.name = None
        self.count = None
        self.cover = None

        self.headers = {
            'x-csrftoken': 'usT80ABkLZRN2ngDTn8kxEsNRS4iG9qx',
            'x-ig-app-id': '936619743392459',
        }
        
    def extract_tag(self, url):
        pattern = r'explore/tags/([^/]+)/?'
        match = re.search(pattern, url)
        return match.group(1)

    async def get_data(self, data):
        if not data:
            async with aiohttp.ClientSession() as client:
                params = {
                    'tag_name': self.tag,
                }
                response = await client.get('https://www.instagram.com/api/v1/tags/web_info/', params=params, headers=self.headers, cookies=self.parent.cookies)
                self.parent.data = await response.json()
        
        self.name = self.parent.data["data"]["name"]
        self.count = self.parent.data["count"]
        self.pk = self.parent.data["data"]["id"]
        self.cover = self.parent.data["data"]["profile_pic_url"]
        self.parent.data["pk"] = self.pk
    
    async def readable_number(self, number):
        number_str = str(number)
        groups = []
        while number_str:
            groups.append(number_str[-3:])
            number_str = number_str[:-3]
        return ' '.join(reversed(groups))
    
    async def create_caption(self, lang):
        return f'<u><b>Instagram Tag</b></u>\n🔗 <a href="{self.parent.link}">{self.name}</a>\n📈 {await _("00033", lang)}: {await self.readable_number(self.count)}'

    async def get_cover(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.cover, cookies=self.parent.cookies)
            self.thumbnail = BufferedInputFile(response.content, 'thumbnail')
            return self.thumbnail