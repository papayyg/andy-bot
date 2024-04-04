import shutil
import os
import re
import uuid
import httpx
import json
import base64
from bs4 import BeautifulSoup

from .api.user import User
from .api.post import Post
from .api.stories import Stories
from .api.music import Music
from .api.locations import Locations
from .api.tags import Tags
from config import INST_SESSION
from utils.db import instagram
from locales.translations import _

cookies = {
    'sessionid': INST_SESSION,
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
}

class InstagramAPI:
    def __init__(self, message) -> None:
        self.message = message
        self.unique_id = uuid.uuid4().hex
        self.text = message.text
        self.path = f'temp/{self.unique_id}'
        self.link = None
        self.main_link = None
        self.data = None
        self.type = None
        self.create_time = None
        self.file_id = None
        self.cookies = cookies
        self.headers = headers

    async def __aenter__(self):
        os.makedirs(f'temp/{self.unique_id}')
        await self.extract_instagram_link()
        await self.check_link()
        await self.get_type()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        shutil.rmtree(f'temp/{self.unique_id}')
        if self.type in ['carousel', 'video', 'image', 'stories-video', 'stories-image', 'highlights-video', 'highlights-image', 'audio', 'locations', 'tags']:
            await self.save()

    async def get_profile(pk, lang):
        data = (await instagram.pk_exists(pk))["data"]
        if 'owner' in data:
            data = data["owner"]
        elif 'user' in data:
            data = data['user']
        user = User(data)
        await user.get_data()
        caption = await user.create_caption(lang)
        avatar = await user.get_avatar()
        return avatar, caption

    async def check_link(self):
        result = await instagram.data_exists(self.link)
        if result:
            self.data = result["data"]
            self.file_id = result["file_id"]
            
    async def extract_instagram_link(self):
        start_index = self.text.find("instagram.com")
        
        left_space_index = self.text.rfind(" ", 0, start_index) 
        if left_space_index == -1:
            left_space_index = 0
        right_space_index = self.text.find(" ", start_index)
        if right_space_index == -1:
            right_space_index = len(self.text)
        
        final_str = self.text[left_space_index:right_space_index].strip()
        if not final_str.startswith('https://'):
            final_str = f'https://{final_str}'
        if '?' in final_str and '/s/' not in final_str:
            final_str = final_str.split('?')[0]

        self.link = final_str
    
    async def get_type(self):
        if '/p/' in self.link or '/reel/' in self.link:
            self.post = Post(self.link)
            self.post.parent = self
            await self.post.get_data(self.data)
        elif '/audio/' in self.link:
            self.type = 'audio'
            self.audio = Music(self.link)
            self.audio.parent = self
            await self.audio.get_music_id()
            await self.audio.get_data(self.data)
        elif '/stories/' in self.link or '/s/' in self.link:
            self.main_link = self.link
            if '/s/' in self.link:
                await self.decode_highlights_id()
            self.stories = Stories(self.link)
            self.stories.parent = self
            await self.stories.get_data(self.data)
        elif '/tags/' in self.link:
            self.type = 'tags'
            self.tags = Tags(self.link)
            self.tags.parent = self
            await self.tags.get_data(self.data)
        elif '/locations/' in self.link:
            self.type = 'locations'
            self.locations = Locations(self.link)
            self.locations.parent = self
            await self.locations.get_data(self.data)
        else:
            self.type = 'profile'
            self.user = User({})
            self.user.parent = self
            await self.user.extract_profile_name()
            await self.user.get_data()

    async def decode_highlights_id(self):
        pattern = r'story_media_id=(\d+)'
        match = re.search(pattern, self.link)
        if match:
            self.pk = match.group(1)
        code = self.link.split("/s/")[1].split("?")[0]
        highlights_id = base64.b64decode(code).decode('utf-8').split(":")[1]
        self.link = f'https://www.instagram.com/stories/highlights/{highlights_id}/'
    
    async def readable_number(number):
        number_str = str(number)
        groups = []
        while number_str:
            groups.append(number_str[-3:])
            number_str = number_str[:-3]
        return ' '.join(reversed(groups))
    
    async def get_stats(pk, lang):
        result = (await instagram.pk_exists(pk))["data"]
        text = f'{result["taken_at"]}\n\n'
        text += f'❤️ {await _("00014", lang)} - {await InstagramAPI.readable_number(result["like_count"])}\n'
        text += f'💬 {await _("00015", lang)} - {await InstagramAPI.readable_number(result["comment_count"])}\n'
        return text
    
    async def get_comments(pk, count):
        link = (await instagram.pk_exists(pk))["_id"]
        async with httpx.AsyncClient() as client:
            response = await client.get(link, cookies=cookies, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            script_tags = soup.find_all('script')
            target_script = None
            for script_tag in script_tags:
                if 'xdt_api__v1__media__media_id__comments__connection' in str(script_tag):
                    target_script = script_tag.string
                    break
            comments = json.loads(target_script)["require"][0][3][0]["__bbox"]["require"][0][3][1]["__bbox"]["result"]["data"]["xdt_api__v1__media__media_id__comments__connection"]["edges"]
        text = ""
        i = 0
        if comments:
            for comment in comments:
                if i < count:
                    point = f'><b>{comment["node"]["user"]["username"]}</b>\n{comment["node"]["text"]}\n\n'
                    if len(point) > 300:
                        continue
                    text += point
                    i += 1
                else:
                    break
        else:
            text = ''
        return text
    
    async def save(self):
        data = {
            "_id": self.main_link or self.link,
            "pk": self.data["pk"],
            "file_id": self.file_id,
            "data": self.data,
            "type": self.type,
        }
        await instagram.save_data(data)