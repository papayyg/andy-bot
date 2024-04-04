import httpx
import aiofiles
import aiohttp
import re
from aiogram.types import FSInputFile, BufferedInputFile

class Music:
    def __init__(self, link) -> None:
        self.pk = None
        self.link = link
        self.parent = None
        self.title = None

        self.headers = {
            'x-csrftoken': '3F67qrWdaZgj90mmY4VXhbsx2dwpBuAV',
            'x-ig-app-id': '936619743392459',
        }
        
    async def get_music_id(self):
        pattern = r'/audio/(\d+)/?'
        match = re.search(pattern, self.link)
        self.pk = match.group(1)

    async def get_data(self, data):
        if not data:
            async with aiohttp.ClientSession() as client:
                audio_data = {
                    'audio_cluster_id': self.pk,
                    'original_sound_audio_asset_id': self.pk,
                }
                response = await client.post('https://www.instagram.com/api/v1/clips/music/', headers=self.headers, data=audio_data)
                self.parent.data = await response.json()
        
        if self.parent.data["metadata"]["music_info"]:
            ad = self.parent.data["metadata"]["music_info"]["music_asset_info"]
            self.download_url = ad["progressive_download_url"]
            self.title = ad["title"]
            self.artist = ad["display_artist"]
            self.for_caption = ad["display_artist"]
            self.cover = ad["cover_artwork_uri"]
            self.duration = int(ad["duration_in_ms"] / 1000)

        else:
            ad = self.parent.data["metadata"]["original_sound_info"]
            self.download_url = ad["progressive_download_url"]
            self.title = ad["original_audio_title"]
            self.artist = ad["ig_artist"]["username"]
            self.for_caption = ad["ig_artist"]["full_name"]
            self.cover = ad["ig_artist"]["profile_pic_url"]
            self.duration = int(ad["duration_in_ms"] / 1000)

        self.parent.data["pk"] = self.pk
    
    async def create_caption(self):
        return f'👤 <a href="{self.parent.link}">{self.for_caption}</a>'
    
    async def create_group_caption(self, user):
        return f'👤 {user}\n\n🔗 <a href="{self.parent.link}">{self.for_caption}</a>'

    async def get_cover(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.cover, cookies=self.parent.cookies)
            self.thumbnail = BufferedInputFile(response.content, 'thumbnail')
            return self.thumbnail, self.artist, self.title
                
    async def download(self):
        async with httpx.AsyncClient() as client:
            if not self.parent.file_id:
                self.parent.path += "/audio.mp3"

                response = await client.get(self.download_url, cookies=self.parent.cookies)
                async with aiofiles.open(self.parent.path, "wb") as f:
                    await f.write(response.content)
                self.input_file = FSInputFile(self.parent.path, self.artist)
                return self.input_file, self.duration
            else:
                return self.parent.file_id, self.duration
           