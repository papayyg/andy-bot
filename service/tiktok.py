import httpx
import json
import aiofiles
import os
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import unquote_plus

from utils.db.files import save_file, file_exists, add_watermark


class TikTokAPI:
    def __init__(self):
        self.text = None
        self.path = None
        
        self.link = None
        self.data_type = None
        self.result = None
        self.tt_chain_token = None
        self.file_id = None
        self.watermark = None
        self.in_db = False

        self.author = None
        self.duration = None
        self.width = None
        self.height = None
        self.desc_second = None
        self.caption = None
        self.file_name = 'file.mp4'

        self.cover = None
        self.cover_gif = None


    async def initialize(self, message):
        await self.get_tg_data(message)
        await self.extract_tiktok_link()
        await self.check_file_in_db_and_get_data()
        await self.set_info()
        await self.get_caption()

    
    async def initialize_watermark(self, message, link):
        await self.get_tg_data(message, link)
        await self.extract_tiktok_link()
        await self.check_file_in_db_and_get_data(True)
        await self.set_info()
    

    async def set_info(self):
        self.duration = self.result["video"]["duration"]
        self.width = self.result["video"]["width"]
        self.height = self.result["video"]["height"]
        self.desc_second = None
        self.cover = self.result["video"]["cover"]
        self.cover_gif = self.result["video"]["dynamicCover"]


    async def get_caption(self):
        self.author = self.result["author"]["uniqueId"].replace('<', '\\<').replace('>', '\\>')
        desc = self.result["desc"].replace('<', '\\<').replace('>', '\\>')
        if len(desc) > 870:
            self.desc_second = desc[870:]
            desc = desc[:870] 
        self.caption = f'👤 <a href="{self.link}">{self.author}</a>\n\n📝 {desc}'
        

    async def get_tg_data(self, message, data = None):
        self.text = message.text
        if data:
            self.text = data
        self.path = f'temp/tiktok_{message.chat.id + message.message_id}.mp4'


    async def extract_tiktok_link(self):
        start_index = self.text.find("tiktok.com")
        
        left_space_index = self.text.rfind(" ", 0, start_index)
        if left_space_index == -1:
            left_space_index = 0

        right_space_index = self.text.find(" ", start_index)
        if right_space_index == -1:
            right_space_index = len(self.text)

        self.link = self.text[left_space_index:right_space_index].strip()
    

    async def unix_time_to_standard(self, unix_time):
        dt = datetime.fromtimestamp(unix_time)
        formatted_time = dt.strftime("%H:%M - %d.%m.%y")
        return formatted_time
    

    async def get_data(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.link, follow_redirects=True)
            soup = BeautifulSoup(response.text, "html.parser")

            script_tag = soup.find('script', id='__UNIVERSAL_DATA_FOR_REHYDRATION__').contents[0]
            start_index = script_tag.find('{')
            end_index = script_tag.rfind('}') + 1
            
            json_data = script_tag[start_index:end_index]
            data = json.loads(json_data)['__DEFAULT_SCOPE__']

            await self.get_tt_chain_token(response)
            return data


    async def get_tt_chain_token(self, response):
        self.tt_chain_token = response.cookies.get("tt_chain_token")


    async def get_type(self, data):
        if "webapp.video-detail" in data:
            self.data_type = 'video'
            self.result = data["webapp.video-detail"]["itemInfo"]["itemStruct"]
            print(self.result)
        elif "webapp.user-detail" in data:
            self.data_type = 'profile'
            self.result = data["webapp.user-detail"]["userInfo"]
        else:
            self.data_type = 'slide'
            self.result = None

        return self.data_type


    async def get_video(self, watermark):
        cookies = {'tt_chain_token': self.tt_chain_token}
        headers = {'referer': 'https://www.tiktok.com/'}
        endpoint = "playAddr" if not watermark else "downloadAddr"
        download_link = self.result["video"][endpoint]
        decoded_url = unquote_plus(download_link)
        async with httpx.AsyncClient() as client:
            response = await client.get(decoded_url, cookies=cookies, headers=headers)
            async with aiofiles.open(self.path, 'wb') as f:
                await f.write(response.content)


    async def delete_video(self):
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass
        

    async def check_file_in_db_and_get_data(self, watermark = False):
        result = await file_exists(self.link)
        if result:
            self.file_id = result["file_id"]
            self.result = result["result"]
            self.data_type = result["data_type"]
            self.in_db = True
            if result["watermark"]:
                self.watermark = result["watermark"]
            elif watermark:
                self.file_name = self.result["author"]["uniqueId"]
                data = await self.get_data()
                type = await self.get_type(data)
                await self.get_video(watermark)
        else:
            data = await self.get_data()
            type = await self.get_type(data)
            if type == 'video':
                await self.get_video(watermark)


    async def save_data_in_db(self, file_id, watermark_id = 0):
        if not self.in_db or self.watermark:
            data = {
                "link": self.link,
                "file_id": file_id,
                "data_type": self.data_type,
                "watermark": watermark_id,
                "result": self.result
            }
            await save_file(data)
