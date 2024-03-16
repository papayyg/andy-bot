from utils.db import get_locals

locales_dict = {}

async def get_chats_locales():
    chats_local = await get_locals()
    
    global locales_dict
    for chat in chats_local:
        locales_dict[chat["_id"]] = chat["lang"]