from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client: AsyncIOMotorClient = None
db = None


async def init_db():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB]
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.jobs.create_index("is_active")


async def get_db():
    return db


def get_client():
    return client
