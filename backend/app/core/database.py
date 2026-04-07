from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = None
db = None

async def get_db():
    return db

async def init_db():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db_name = settings.MONGODB_URI.rsplit("/", 1)[-1].split("?")[0] or "time_tracker"
    db = client[db_name]
    await db.users.create_index("email", unique=True)
    if not await db.settings.find_one({"key": "app_name"}):
        await db.settings.insert_many([
            {"key": "app_name", "value": "TimeLog"},
            {"key": "org_name", "value": "TimeLog Organization"},
        ])
