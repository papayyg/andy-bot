from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_HOST

cluster = AsyncIOMotorClient(MONGO_HOST)
chats = cluster.AndyBot.chats

async def save_chat_data(chat_data: dict):
    if not await chats.find_one({"_id": chat_data["_id"]}):
        chat_data["date_added"] = datetime.now()
        await chats.insert_one(chat_data)

async def change_language(chat_id: int, new_language: str):
    filter_ = {"_id": chat_id}
    update = {"$set": {"lang": new_language}}
    return await chats.update_one(filter_, update)

async def chat_exists(chat_id: int):
    return await chats.find_one({"_id": chat_id})

async def get_locals():
    projection = {"_id": 1, "lang": 1}
    chats_local = await chats.find({}, projection).to_list(None)
    return chats_local