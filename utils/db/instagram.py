from utils.db.chats import cluster

instagram = cluster.AndyBot.instagram

async def data_exists(link):
	return await instagram.find_one({"_id": link})

async def save_data(data):
	if not await data_exists(data["_id"]):
		await instagram.insert_one(data)

async def pk_exists(pk):
	return await instagram.find_one({"pk": pk})