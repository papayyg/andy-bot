import os
import httpx
import json
import shutil
from bs4 import BeautifulSoup

from .api.video import Video
from .api.user import User
from .api.music import Music

class TikTokAPI:
    def __init__(self, message) -> None:
        self.message = message
        self.chat_id = message.chat.id
        self.text = message.text
        self.path = f'temp/{self.chat_id}'
        self.link = None
        self.data = None
        self.tt_chain_token = None
        self.type = None

        self.video = None

    async def __aenter__(self):
        os.makedirs(f'temp/{self.chat_id}')
        await self.extract_tiktok_link()
        await self.get_scope_data()
        await self.get_type_content()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        shutil.rmtree(f'temp/{self.chat_id}')
        pass
    

    async def extract_tiktok_link(self):
        start_index = self.text.find("tiktok.com")
        
        left_space_index = self.text.rfind(" ", 0, start_index) 
        if left_space_index == -1:
            left_space_index = 0
        right_space_index = self.text.find(" ", start_index)
        if right_space_index == -1:
            right_space_index = len(self.text)
        
        final_str = self.text[left_space_index:right_space_index].strip()
        if not final_str.startswith('https://'):
            final_str = f'https://{final_str}'

        self.link = final_str
    
    async def get_scope_data(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.link, follow_redirects=True)
            soup = BeautifulSoup(response.text, "html.parser")

            script_tag = soup.find('script', id='__UNIVERSAL_DATA_FOR_REHYDRATION__').string
            json_data = script_tag[script_tag.find('{'):script_tag.rfind('}') + 1]

            self.data = json.loads(json_data)['__DEFAULT_SCOPE__']
            self.tt_chain_token = response.cookies.get("tt_chain_token")
      
    async def get_type_content(self):
        if "webapp.video-detail" in self.data:
            self.data_type = 'video'
            self.data = self.data["webapp.video-detail"]["itemInfo"]["itemStruct"]
            self.video = Video(self.data)
            self.author = User(self.data["author"])
            self.music = Music(self.data["music"])
            self.video.parent = self
        elif "webapp.user-detail" in self.data:
            self.data_type = 'profile'
            self.data = self.data["webapp.user-detail"]["userInfo"]
        else:
            self.data_type = 'slide'
            self.data = None
        