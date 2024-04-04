import aiohttp
import re

class Locations:
    def __init__(self, link) -> None:
        self.pk = self.extract_location_id(link)
        self.link = link
        self.parent = None
        self.name = None
        self.category = None
        self.google_link = None

        self.headers = {
            'x-csrftoken': 'usT80ABkLZRN2ngDTn8kxEsNRS4iG9qx',
            'x-ig-app-id': '936619743392459',
        }
        
    def extract_location_id(self, url):
        pattern = r'locations/(\d+)/?'
        match = re.search(pattern, url)
        return match.group(1)

    async def create_google_maps_link(self, lat, lng):
        base_url = "https://www.google.com/maps/search/?api=1&query="
        location = f"{lat},{lng}"
        return base_url + location

    async def get_data(self, data):
        if not data:
            async with aiohttp.ClientSession() as client:
                params = {
                    'location_id': self.pk,
                    'show_nearby': 'false',
                }
                response = await client.get('https://www.instagram.com/api/v1/locations/web_info/', headers=self.headers, params=params)
                self.parent.data = await response.json()
        
        self.name = self.parent.data["native_location_data"]["location_info"]["name"]
        self.category = self.parent.data["native_location_data"]["location_info"]["category"]
        self.google_link = await self.create_google_maps_link(self.parent.data["native_location_data"]["location_info"]["lat"], self.parent.data["native_location_data"]["location_info"]["lng"])
        self.parent.data["pk"] = self.pk
    
    async def create_caption(self):
        return f'<u><b>Instagram Location</b></u>\n🗺 <a href="{self.parent.link}">{self.name}</a> - {self.category}\n📍 <a href="{self.google_link}">Google Link</a>'

    async def create_group_caption(self, user):
        return f'👤 {user}\n\n<u><b>Instagram Location</b></u>\n🗺 <a href="{self.parent.link}">{self.name}</a>\n{self.category}\n📍 <a href="{self.google_link}">Google Link</a>'
