import httpx
import json
import aiofiles
import os
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

from locales.translations import _
from utils.locales import locales_dict
from utils.db.files import save_file, file_exists, add_watermark


class TikTokAPI:
    def __init__(self, lang):
        self.lang = lang
        self.text = None
        self.path = None
        
        self.link = None
        self.data_type = None
        self.result = None
        self.tt_chain_token = None
        self.file_id = None
        self.watermark = None
        self.watermark_id = None
        self.in_db = False

        self.author = None
        self.duration = None
        self.width = None
        self.height = None
        self.desc_second = None
        self.caption = None
        self.file_name = 'file'

        self.cover = None
        self.cover_gif = None

    async def initialize(self, message, link = None):
        await self.get_tg_data(message, link)
        await self.check_file_in_db_and_get_data()
        await self.set_info()
        await self.get_caption()

    
    async def initialize_watermark(self, message, link):
        await self.get_tg_data(message, link)
        await self.check_file_in_db_and_get_data()
        await self.set_info()
    

    async def set_info(self):
        if self.data_type == 'video':
            self.duration = self.result["video"]["duration"]
            self.width = self.result["video"]["width"]
            self.height = self.result["video"]["height"]
            self.desc_second = None
            self.cover = self.result["video"]["cover"]
            self.cover_gif = self.result["video"]["dynamicCover"]


    async def get_caption(self):
        if self.data_type == 'profile':
            await self.get_profile_caption()
            return
        self.author = self.result["author"]["uniqueId"].replace('<', '\\<').replace('>', '\\>')
        desc = self.result["desc"].replace('<', '\\<').replace('>', '\\>')
        if len(desc) > 870:
            self.desc_second = desc[870:]
            desc = desc[:870] 
        self.caption = f'👤 <a href="{self.link}">{self.author}</a>\n\n📝 {desc}'

    async def get_profile_caption(self):
        self.author = self.result["user"]["uniqueId"]
        link = f'➡️ tiktok.com/@{self.author}'
        titke = f'👤 <b>{self.result["user"]["nickname"]}</b>\n{link}'
        desc = f'\n\n{self.result["user"]["signature"]}' if self.result["user"]["signature"] != '' else ''
        bio_link = f'\n\n🔗 {self.result["user"]["bioLink"]["link"]}' if "bioLink" in self.result["user"] else ''
        
        follower = f'<i>{await _("00007", self.lang)} - {await self.readable_number(self.result["stats"]["followerCount"])}</i>'
        following = f'<i>{await _("00008", self.lang)} - {await self.readable_number(self.result["stats"]["followingCount"])}</i>'
        heart = f'<i>{await _("00009", self.lang)} - {await self.readable_number(self.result["stats"]["heartCount"])}</i>'
        video = f'<i>{await _("00010", self.lang)} - {await self.readable_number(self.result["stats"]["videoCount"])}</i>'
        stats = f'\n\n🔎 <u>{await _("00011", self.lang)}:</u>\n{follower}\n{following}\n{heart}\n{video}'

        self.caption = f'{titke}{desc}{bio_link}{stats}'
        

    async def get_tg_data(self, message, link):
        if link:
            self.link = link
        else:
            self.link = await self.extract_tiktok_link(message.text)
        self.path = f'temp/tiktok_{message.chat.id + message.message_id}'


    async def extract_tiktok_link(self, text):
        start_index = text.find("tiktok.com")
        
        left_space_index = text.rfind(" ", 0, start_index)
        if left_space_index == -1:
            left_space_index = 0

        right_space_index = text.find(" ", start_index)
        if right_space_index == -1:
            right_space_index = len(text)

        return text[left_space_index:right_space_index].strip()
    
    async def readable_number(self, number):
        number_str = str(number)
        groups = []
        while number_str:
            groups.append(number_str[-3:])
            number_str = number_str[:-3]
        return ' '.join(reversed(groups))

    async def unix_time_to_standard(self, unix_time):
        dt = datetime.fromtimestamp(int(unix_time))
        formatted_time = dt.strftime("%H:%M - %d.%m.%y")
        return formatted_time
    
    async def get_stats(self, link):
        result = (await file_exists(link))["result"]
        create_time = await self.unix_time_to_standard(result["createTime"])
        stats = result["stats"]
        text = f'{create_time}\n\n'
        text += f'❤️ {await _("00014", self.lang)} - {await self.readable_number(stats["diggCount"])}\n'
        text += f'💬 {await _("00015", self.lang)}  - {await self.readable_number(stats["commentCount"])}\n'
        text += f'📣 {await _("00016", self.lang)}  - {await self.readable_number(stats["shareCount"])}\n'
        text += f'▶️ {await _("00017", self.lang)}  - {await self.readable_number(stats["playCount"])}\n'
        text += f'🌟 {await _("00018", self.lang)}  - {await self.readable_number(stats["collectCount"])}\n'
        return text
    

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
        elif "webapp.user-detail" in data:
            self.data_type = 'profile'
            self.result = data["webapp.user-detail"]["userInfo"]
        else:
            self.data_type = 'slide'
            self.result = None

        return self.data_type


    async def get_video(self):
        self.path += '.mp4'
        cookies = {'tt_chain_token': self.tt_chain_token}
        headers = {'referer': 'https://www.tiktok.com/'}
        endpoint = "playAddr" if not self.watermark else "downloadAddr"
        download_link = self.result["video"][endpoint]
        async with httpx.AsyncClient() as client:
            response = await client.get(download_link, cookies=cookies, headers=headers)
            async with aiofiles.open(self.path, 'wb') as f:
                await f.write(response.content)

    async def get_photo(self):
        self.path += '.jpg'
        headers = {'referer': 'https://www.tiktok.com/'}
        download_link = self.result["user"]["avatarLarger"]
        async with httpx.AsyncClient() as client:
            response = await client.get(download_link, headers=headers)
            async with aiofiles.open(self.path, 'wb') as f:
                await f.write(response.content)

    async def delete_file(self):
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass
        

    async def check_file_in_db_and_get_data(self):
        result = await file_exists(self.link)
        if result:
            self.file_id = result["file_id"]
            self.result = result["result"]
            self.data_type = result["data_type"]
            self.in_db = True
            
            if result["watermark"]:
                self.watermark_id = result["watermark"]
            elif self.watermark:
                self.file_name = self.result["author"]["uniqueId"]
                self.tt_chain_token = result["tt_chain_token"]
                await self.get_video()
        else:
            data = await self.get_data()
            type = await self.get_type(data)
            
            if type == 'video':
                await self.get_video()
            elif type == 'profile':
                await self.get_photo()


    async def save_data_in_db(self, file_id):
        if not self.in_db:
            data = {
                "link": self.link,
                "file_id": file_id,
                "data_type": self.data_type,
                "watermark": None,
                "result": self.result,
                "tt_chain_token": self.tt_chain_token
            }
            await save_file(data)
        elif not self.watermark_id:
            await add_watermark(self.link, file_id)


    async def get_videos(self, url):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            await browser.new_context()
            context  = await browser.new_context(**p.devices['Desktop Chrome'])
            page = await context.new_page()
            await stealth_async(page)

            async def save_responses_and_body(response):
                try:
                    if response.url.startswith("https://www.tiktok.com/api/post/item_list"):
                        body = await response.body()
                        regular_string = body.decode('utf-8')
                        json_data = json.loads(regular_string)
                        print(json_data)

                        cookies = await page.context.cookies()
                        tt_chain_token = None
                        for cookie in cookies:
                            if cookie['name'] == 'tt_chain_token':
                                tt_chain_token = cookie["value"]
                                break
                        print(tt_chain_token)
                except:
                    pass
            page.on("response", save_responses_and_body)
            
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
          



