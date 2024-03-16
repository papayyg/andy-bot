import httpx
import json
import aiofiles
import os
from bs4 import BeautifulSoup
from datetime import datetime

async def extract_tiktok_link(text):
    start_index = text.find("tiktok.com")
    
    left_space_index = text.rfind(" ", 0, start_index)
    if left_space_index == -1:
        left_space_index = 0

    right_space_index = text.find(" ", start_index)
    if right_space_index == -1:
        right_space_index = len(text)

    tiktok_link = text[left_space_index:right_space_index].strip()
    
    return tiktok_link

async def unix_time_to_standard(unix_time):
    dt = datetime.fromtimestamp(unix_time)
    formatted_time = dt.strftime("%H:%M - %d.%m.%y")
    return formatted_time


async def get_data(link):
    async with httpx.AsyncClient() as client:
        response = await client.get(link, follow_redirects=True)
        soup = BeautifulSoup(response.text, "html.parser")

        script_tag = soup.find('script', id='__UNIVERSAL_DATA_FOR_REHYDRATION__').contents[0]
        start_index = script_tag.find('{')
        end_index = script_tag.rfind('}') + 1
        
        json_data = script_tag[start_index:end_index]
        data = json.loads(json_data)['__DEFAULT_SCOPE__']

        tt_chain_token = response.cookies.get("tt_chain_token")
        if "webapp.video-detail" in data:
            data_type = 'video'
            result = data["webapp.video-detail"]["itemInfo"]["itemStruct"]
        elif "webapp.user-detail" in data:
            data_type = 'profile'
            result = data["webapp.user-detail"]["userInfo"]
        else:
            data_type = 'slide'
            result = None
        return data_type, result, tt_chain_token
    

async def get_video(link, tt_chain_token, path):
    cookies = {'tt_chain_token': tt_chain_token}
    headers = {'referer': 'https://www.tiktok.com/'}
    async with httpx.AsyncClient() as client:
        response = await client.get(link, cookies=cookies, headers=headers)
        async with aiofiles.open(path, 'wb') as f:
            await f.write(response.content)


async def delete_video(file_path):
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass