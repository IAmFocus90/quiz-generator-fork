from motor.motor_asyncio import AsyncIOMotorCollection


async def ensure_quizzes_v2_indexes(collection: AsyncIOMotorCollection):
    await collection.create_index([("owner_user_id", 1), ("created_at", -1)])
    await collection.create_index([("visibility", 1), ("created_at", -1)])
    await collection.create_index("status")
    await collection.create_index([("source", 1), ("created_at", -1)])


async def ensure_folders_v2_indexes(collection: AsyncIOMotorCollection):
    await collection.create_index([("user_id", 1), ("name", 1)], unique=True)


async def ensure_folder_items_v2_indexes(collection: AsyncIOMotorCollection):
    await collection.create_index([("folder_id", 1), ("quiz_id", 1)], unique=True)
    await collection.create_index([("folder_id", 1), ("position", 1)])


async def ensure_saved_quizzes_v2_indexes(collection: AsyncIOMotorCollection):
    await collection.create_index([("user_id", 1), ("quiz_id", 1)], unique=True)
    await collection.create_index([("user_id", 1), ("saved_at", -1)])


async def ensure_quiz_history_v2_indexes(collection: AsyncIOMotorCollection):
    await collection.create_index([("user_id", 1), ("created_at", -1)])
    await collection.create_index([("quiz_id", 1), ("created_at", -1)])
    await collection.create_index([("action", 1), ("created_at", -1)])
