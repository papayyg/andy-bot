import os
import httpx
import json
import shutil
import uuid
import aiofiles
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from aiogram.types import FSInputFile

from .api.video import Video
from .api.user import User
from .api.music import Music
from .api.slides import Slides
from .api.challenge import Challenge
from utils.db import tiktok

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
        self.mobile = False
        self.challenge = False

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
    
    async def get_scope_data(self, step = False):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(self.link, follow_redirects=True, headers=headers)
                soup = BeautifulSoup(response.text, "html.parser")
                script_tag = soup.find('script', id='__UNIVERSAL_DATA_FOR_REHYDRATION__')

                if script_tag is None:
                    print(f"[TikTok ERROR] Script tag not found for {self.link}")
                    print(f"[TikTok ERROR] Status: {response.status_code}, Final URL: {response.url}")
                    print(f"[TikTok ERROR] Response (first 1000 chars): {response.text[:1000]}")
                    self.type = 'live'
                    return

                json_data = script_tag.string[script_tag.string.find('{'):script_tag.string.rfind('}') + 1]

                self.data = json.loads(json_data)['__DEFAULT_SCOPE__']
                self.tt_chain_token = response.cookies.get("tt_chain_token")

                if step: return
                await self.split_data()
        except Exception as e:
            print(f"[TikTok ERROR] get_scope_data exception for {self.link}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self.type = 'live'
            return

    async def redirect(self):
        self.link = f'https://www.tiktok.com{self.data["webapp.browserRedirect-context"]["browserRedirectUrl"]}'
        await self.get_scope_data(True)

    async def split_data(self):
        if "webapp.browserRedirect-context" in self.data:
            await self.redirect()
        if "webapp.video-detail" in self.data and "itemInfo" in self.data["webapp.video-detail"]:
            self.type = 'video'
            self.data = self.data["webapp.video-detail"]["itemInfo"]["itemStruct"]
        elif "webapp.user-detail" in self.data or self.type == 'profile':
            self.type = 'profile'
            self.data = self.data["webapp.user-detail"]["userInfo"]
        elif "playlist" in self.data["seo.abtest"]["canonical"]:
            self.type = 'playlist'
            return
        else:
            if "webapp.video-detail" in self.data and "itemInfo" not in self.data["webapp.video-detail"]:
                self.mobile = True
            pass
        
    async def get_type_content(self):
        if self.link in ['https://www.tiktok.com/', 'https://www.tiktok.com', 'www.tiktok.com/', 'www.tiktok.com', 'tiktok.com/', 'tiktok.com']:
            self.type = 'None'
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
            if not self.type:
                if not self.mobile:
                    await self.browser_initialization()
                else:
                    self.type = 'stories'
                    await self.sstick_get()
                    return
            await self.get_sub_type()

    async def get_sub_type(self):
        if self.type == 'live':
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

    async def sstick_get(self):
        headers = {
            'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        }
        params = { 'url': 'dl' }
        data = {
            'id': self.link,
            'locale': 'ru',
            'tt': 'eG1ISHQ1',
        }
        async with httpx.AsyncClient() as client:
            response = await client.post('https://ssstik.io/abc', params=params,headers=headers, data=data)
            soup = BeautifulSoup(response.text, 'html.parser')
            self.download_link = soup.find('a', class_='without_watermark').get('href')
            self.author = soup.find('h2').text

    async def ssstik_download(self, user = False):
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
        

    async def browser_initialization(self):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                context = await browser.new_context(
                    **{
                        **p.devices['Desktop Chrome'],
                        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'viewport': {'width': 1920, 'height': 1080},
                        'screen': {'width': 1920, 'height': 1080},
                        'extra_http_headers': {
                            'Accept-Language': 'en-US,en;q=0.9',
                            'sec-ch-ua-platform': '"Windows"'
                        }
                    }
                )
                
                page = await context.new_page()
                await stealth_async(page)
                
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'platform', {
                        get: function() { return 'Win32'; }
                    });
                    Object.defineProperty(navigator, 'userAgentData', {
                        get: function() { 
                            return { 
                                platform: 'Windows',
                                brands: [
                                    {brand: 'Chromium', version: '120'},
                                    {brand: 'Google Chrome', version: '120'},
                                    {brand: 'Not-A.Brand', version: '99'}
                                ]
                            }; 
                        }
                    });
                """)
                
                self.challenge = False
                
                async def save_responses_and_body(response):
                    if response.url.startswith("https://www.tiktok.com/api/item/detail/") or response.url.startswith("https://www.tiktok.com/api/music/detail/"):
                        body = await response.body()
                        regular_string = body.decode('utf-8')
                        self.data = json.loads(regular_string)

                        cookies = await page.context.cookies()
                        for cookie in cookies:
                            if cookie['name'] == 'tt_chain_token':
                                self.tt_chain_token = cookie["value"]
                                break
                        page.remove_listener("response", save_responses_and_body)
                        await browser.close()
                    elif response.url.startswith("https://www.tiktok.com/api/challenge/detail/"):
                        body = await response.body()
                        regular_string = body.decode('utf-8')
                        self.data = json.loads(regular_string)

                        cookies = await page.context.cookies()
                        for cookie in cookies:
                            if cookie['name'] == 'tt_chain_token':
                                self.tt_chain_token = cookie["value"]
                                break
                        self.challenge = True
                    elif response.url.startswith("https://www.tiktok.com/api/challenge/item_list/") and self.challenge:
                        body = await response.body()
                        regular_string = body.decode('utf-8')
                        self.content = json.loads(regular_string)["itemList"][0]
                        
                        page.remove_listener("response", save_responses_and_body)
                        await browser.close()
        
                page.on("response", save_responses_and_body)
                
                await page.goto(self.link)
                await page.wait_for_selector(".swiper-wrapper")
        except Exception as e:
            print(f"Error in browser initialization: {e}")

    async def save(self):
        data = {
            "_id": self.link,
            "data": self.data,
            "tt_chain_token": self.tt_chain_token,
            "type": self.type,
        }
        await tiktok.save_link(data)