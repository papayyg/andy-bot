import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = str(os.getenv("BOT_TOKEN"))
# TEST_TOKEN = str(os.getenv("TEST_TOKEN"))
MONGO_HOST = str(os.getenv("MONGO_HOST"))
# owner_id = int(os.getenv("owner_id"))
INST_SESSION = str(os.getenv("INST_SESSION"))