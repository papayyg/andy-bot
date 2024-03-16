from utils.db.chats import cluster

files = cluster.AndyBot.files

async def save_file(tiktok_link, file_id, data_type, result):
	data = {
		"link": tiktok_link,
		"file_id": file_id,
		"data_type": data_type,
		"result": result
	}
	await files.insert_one(data)

async def add_watermark(tiktok_link, file_id):
	await files.update_one({"link": tiktok_link}, {"$set": {"watermark": file_id}})


async def file_exists(tiktok_link):
	return await files.find_one({"link": tiktok_link})