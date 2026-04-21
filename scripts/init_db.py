import asyncio
from app.database import engine
from app.models.notification import Base
from app.models.notification import Notification

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully")

if __name__ == "__main__":
    asyncio.run(init())