import os
import httpx
import shutil
import uuid
import aiofiles
import logging
from bs4 import BeautifulSoup
from aiogram.types import FSInputFile

from .api.video import Video
from .api.user import User
from .api.music import Music
from .api.slides import Slides
from .api.challenge import Challenge
from utils.db import tiktok

logger = logging.getLogger(__name__)


class TikTokAPI:
    video = Video
    user = User
    music = Music
    slides = Slides
    challenge = Challenge

    def __init__(self, message) -> None:
        self.message = message
        self.unique_id = uuid.uuid4().hex
        self.text = message.text
        self.path = f'temp/{self.unique_id}'
        self.link = None
        self.data = None
        self.content = None
        self.tt_chain_token = None
        self.type = None

    async def __aenter__(self):
        os.makedirs(f'temp/{self.unique_id}')
        await self.extract_tiktok_link()
        if not await self.check_link():
            await self.get_scope_data()
        await self.get_type_content()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        shutil.rmtree(f'temp/{self.unique_id}')
        if self.type not in ['challenge', 'stories']:
            await self.save()

    async def check_link(self):
        r = await tiktok.link_exists(self.link)
        if r:
            self.data = r["data"]
            self.tt_chain_token = r["tt_chain_token"]
            self.type = r["type"]
        return r

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

    def _is_profile_url(self):
        return (
            '/@' in self.link
            and '/video/' not in self.link
            and '/music/' not in self.link
            and '/tag/' not in self.link
        )

    async def get_scope_data(self):
        if self._is_profile_url():
            await self._get_profile_via_tikwm()
        else:
            await self._get_post_via_tikwm()

    async def _get_post_via_tikwm(self):
        """Получаем данные о посте (видео/слайды) через tikwm.com."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    'https://www.tikwm.com/api/',
                    data={'url': self.link, 'hd': 1},
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    },
                )
                result = response.json()

            if result.get('code') != 0:
                logger.error("[TikTok] tikwm API error for %s: %s", self.link, result.get('msg'))
                self.type = 'live'
                return

            d = result['data']
            mi = d.get("music_info", {})
            author = {
                "id": d["author"]["id"],
                "uniqueId": d["author"]["unique_id"],
                "nickname": d["author"]["nickname"],
                "avatarLarger": d["author"]["avatar"],
                "signature": "",
            }
            music = {
                "id": str(mi.get("id", "")),
                "authorName": mi.get("author", ""),
                "title": mi.get("title", ""),
                "playUrl": mi.get("play", d.get("music", "")),
                "coverLarge": mi.get("cover", d.get("cover", "")),
                "duration": mi.get("duration", d.get("duration", 0)),
            }
            stats = {
                "diggCount": str(d.get("digg_count", 0)),
                "commentCount": str(d.get("comment_count", 0)),
                "playCount": str(d.get("play_count", 0)),
                "shareCount": str(d.get("share_count", 0)),
                "collectCount": str(d.get("collect_count", 0)),
            }

            if d.get("images"):
                item_struct = {
                    "id": d["id"],
                    "desc": d["title"],
                    "createTime": str(d["create_time"]),
                    "statsV2": stats,
                    "imagePost": {
                        "images": [
                            {"imageURL": {"urlList": [img_url]}}
                            for img_url in d["images"]
                        ]
                    },
                    "author": author,
                    "music": music,
                }
                self.data = {"itemInfo": {"itemStruct": item_struct}}
                self.type = None  # get_sub_type разберёт itemInfo → slides
            else:
                self.data = {
                    "id": d["id"],
                    "desc": d["title"],
                    "createTime": str(d["create_time"]),
                    "video": {
                        "height": d.get("height", 1024),
                        "width": d.get("width", 576),
                        "duration": d["duration"],
                        "cover": d["cover"],
                        "dynamicCover": d.get("ai_dynamic_cover", d["cover"]),
                        "playAddr": d["play"],
                        "downloadAddr": d["wmplay"],
                    },
                    "statsV2": stats,
                    "author": author,
                    "music": music,
                }
                self.type = "video"

            logger.info("[TikTok] tikwm succeeded for %s (type=%s)", self.link, self.type or 'slides')
        except Exception as e:
            logger.exception("[TikTok] tikwm post failed for %s: %s", self.link, e)
            self.type = 'live'

    async def _get_profile_via_tikwm(self):
        """Получаем профиль пользователя через tikwm.com."""
        try:
            unique_id = self.link.split('/@')[1].split('/')[0].split('?')[0]
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    'https://www.tikwm.com/api/user/info',
                    params={'unique_id': unique_id},
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    },
                )
                result = response.json()

            if result.get('code') != 0:
                logger.error("[TikTok] tikwm user/info error for %s: %s", self.link, result.get('msg'))
                self.type = 'live'
                return

            d = result['data']
            user = d['user']
            stats = d['stats']

            self.data = {
                "user": {
                    "id": user.get("id", ""),
                    "uniqueId": user.get("uniqueId", unique_id),
                    "nickname": user.get("nickname", unique_id),
                    "avatarLarger": (
                        user.get("avatarLarger")
                        or user.get("avatarMedium")
                        or user.get("avatarThumb", "")
                    ),
                    "signature": user.get("signature", ""),
                    "bioLink": user.get("bioLink"),
                },
                "stats": {
                    "followerCount": stats.get("followerCount", 0),
                    "followingCount": stats.get("followingCount", 0),
                    "heartCount": stats.get("heartCount", 0),
                    "videoCount": stats.get("videoCount", 0),
                },
            }
            self.type = 'profile'
            logger.info("[TikTok] tikwm profile succeeded for %s", self.link)
        except Exception as e:
            logger.exception("[TikTok] tikwm profile failed for %s: %s", self.link, e)
            self.type = 'live'

    async def get_type_content(self):
        if self.link in ['https://www.tiktok.com/', 'https://www.tiktok.com', 'www.tiktok.com/', 'www.tiktok.com', 'tiktok.com/', 'tiktok.com']:
            self.type = 'None'
            return
        if not self.type and isinstance(self.data, dict):
            await self.get_sub_type()
            return
        if self.type == 'video':
            self.video = Video(self.data)
            self.user = User(self.data["author"])
            self.music = Music(self.data["music"])
            self.video.parent = self
            self.music.parent = self
        elif self.type == 'profile':
            self.user = User(self.data["user"])
            self.user.parent = self
            self.user.stats = self.data["stats"]
            self.user.bio_links = self.data["user"].get("bioLink")
        else:
            await self.get_sub_type()

    async def get_sub_type(self):
        if self.type == 'live':
            return
        if not isinstance(self.data, dict):
            self.type = 'live'
            return
        if 'itemInfo' in self.data:
            data = self.data["itemInfo"]["itemStruct"]
            self.type = 'slides'
            self.slides = Slides(data)
            self.user = User(data["author"])
            self.music = Music(data["music"])
            self.music.parent = self
            self.slides.parent = self
        elif 'musicInfo' in self.data:
            data = self.data["musicInfo"]
            self.type = 'music'
            self.user = User(data["author"])
            self.music = Music(data["music"])
            self.music.parent = self
            self.user.parent = self
            self.music.stats = data["stats"]["videoCount"]
        elif 'challengeInfo' in self.data:
            data = self.data["challengeInfo"]
            self.type = 'challenge'
            self.challenge = Challenge(data)
            self.challenge.parent = self
            self.video = Video(self.content)
            self.user = User(self.content["author"])
            self.video.parent = self
        else:
            self.type = 'live'

    async def sstick_get(self):
        headers = {
            'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        }
        params = {'url': 'dl'}
        data = {
            'id': self.link,
            'locale': 'ru',
            'tt': 'eG1ISHQ1',
        }
        async with httpx.AsyncClient() as client:
            response = await client.post('https://ssstik.io/abc', params=params, headers=headers, data=data)
            soup = BeautifulSoup(response.text, 'html.parser')
            self.download_link = soup.find('a', class_='without_watermark').get('href')
            self.author = soup.find('h2').text

    async def ssstik_download(self, user=False):
        self.path += "/video.mp4"
        async with httpx.AsyncClient() as client:
            response = await client.get(self.download_link)
            async with aiofiles.open(self.path, "wb") as f:
                await f.write(response.content)
        if not user:
            caption = f'👤 <a href="{self.link}">{self.author}</a>'
        else:
            caption = f'👤 {user}\n\n🔗 <a href="{self.link}">{self.author}</a>'
        return FSInputFile(self.path, self.author), caption

    async def save(self):
        data = {
            "_id": self.link,
            "data": self.data,
            "tt_chain_token": self.tt_chain_token,
            "type": self.type,
        }
        await tiktok.save_link(data)
