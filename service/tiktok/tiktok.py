import os
import httpx
import json
import shutil
import uuid
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

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

    async def __aenter__(self):
        os.makedirs(f'temp/{self.unique_id}')
        await self.extract_tiktok_link()
        if not await self.check_link():
            await self.get_scope_data()
        await self.get_type_content()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        shutil.rmtree(f'temp/{self.unique_id}')
        if self.type != 'challenge':
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
        async with httpx.AsyncClient() as client:
            response = await client.get(self.link, follow_redirects=True)
            soup = BeautifulSoup(response.text, "html.parser")

            script_tag = soup.find('script', id='__UNIVERSAL_DATA_FOR_REHYDRATION__').string
            json_data = script_tag[script_tag.find('{'):script_tag.rfind('}') + 1]

            self.data = json.loads(json_data)['__DEFAULT_SCOPE__']
            self.tt_chain_token = response.cookies.get("tt_chain_token")

            if step: return
            await self.split_data()

    async def redirect(self):
        self.link = f'https://www.tiktok.com{self.data["webapp.browserRedirect-context"]["browserRedirectUrl"]}'
        await self.get_scope_data(True)

    async def split_data(self):
        if "webapp.browserRedirect-context" in self.data:
            await self.redirect()
        if "webapp.video-detail" in self.data:
            self.type = 'video'
            self.data = self.data["webapp.video-detail"]["itemInfo"]["itemStruct"]
        elif "webapp.user-detail" in self.data or self.type == 'profile':
            self.type = 'profile'
            self.data = self.data["webapp.user-detail"]["userInfo"]
        else:
            pass
        
    async def get_type_content(self):
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
            self.bio_links = self.data["user"].get("bioLink")
        else:
            if not self.type:
                await self.browser_initialization()
            await self.get_sub_type()

    async def get_sub_type(self):
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


    async def browser_initialization(self):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                await browser.new_context()
                context  = await browser.new_context(**p.devices['Desktop Chrome'])
                page = await context.new_page()
                await stealth_async(page)
                challenge = False
                async def save_responses_and_body(response):
                    global challenge
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
                        challenge = True
                    elif response.url.startswith("https://www.tiktok.com/api/challenge/item_list/") and challenge:
                        body = await response.body()
                        regular_string = body.decode('utf-8')
                        self.content = json.loads(regular_string)["itemList"][0]
                        
                        page.remove_listener("response", save_responses_and_body)
                        await browser.close()
        
                page.on("response", save_responses_and_body)
                
                await page.goto(self.link)
                # await page.wait_for_load_state("networkidle")
                await page.wait_for_selector(".swiper-wrapper")
        except:
            pass

    async def save(self):
        data = {
            "_id": self.link,
            "data": self.data,
            "tt_chain_token": self.tt_chain_token,
            "type": self.type,
        }
        await tiktok.save_link(data)