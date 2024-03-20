from utils.db.chats import cluster

links = cluster.AndyBot.links
videos = cluster.AndyBot.videos
musics = cluster.AndyBot.musics

async def link_exists(link):
	return await links.find_one({"_id": link})

async def save_link(data):
	if not await link_exists(data["_id"]):
		await links.insert_one(data)

async def id_exists(id):
	return await videos.find_one({"_id": id})

async def music_exists(id):
	return await musics.find_one({"_id": id})

async def save_video(data):
	if not await id_exists(data["_id"]):
		await videos.insert_one(data)

async def save_music(data):
	if not await music_exists(data["_id"]):
		await musics.insert_one(data)

async def get_tt_chain_token(id):
	return await links.find_one({'data.id': id})

async def set_watermark_id(id, file_id):
	await videos.update_one(
        {"_id": id},
        {"$set": {"watermark_file_id": file_id}}
    )

async def get_data_by_token(token):
	return await links.find_one({"tt_chain_token": token})