import os
import asyncio
import importlib.util
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGO_DB", "quiz_db")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "quizzes")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DATABASE_NAME]
quiz_collection = db[COLLECTION_NAME]

BASE_PATH = os.path.dirname(__file__)
CATEGORIES_PATH = os.path.join(BASE_PATH, "categories")

async def seed_subcategory(category, subcategory):
    print(f"🔍 Processing {category}/{subcategory}")

    # Skip if already seeded
    existing = await quiz_collection.count_documents({
        "category": category,
        "subcategory": subcategory
    })
    if existing > 0:
        print(f"⏭️  Already seeded: {category}/{subcategory} — Skipping")
        return

    # Dynamically load the question data
    module_path = os.path.join(CATEGORIES_PATH, category, subcategory, "questions.py")
    if not os.path.exists(module_path):
        print(f"⚠️  File not found: {module_path}")
        return

    spec = importlib.util.spec_from_file_location("questions", module_path)
    questions_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(questions_module)

    if not hasattr(questions_module, "data") or not isinstance(questions_module.data, list):
        print(f"⚠️  'data' variable missing or invalid in {module_path}")
        return

    data = questions_module.data

    for q in data:
        q["category"] = category
        q["subcategory"] = subcategory

    if data:
        await quiz_collection.insert_many(data)
        print(f"✅ Seeded {len(data)} questions in {category}/{subcategory}")
    else:
        print(f"⚠️  No questions found in {category}/{subcategory}")

async def main():
    for category in os.listdir(CATEGORIES_PATH):
        category_path = os.path.join(CATEGORIES_PATH, category)
        if not os.path.isdir(category_path):
            continue

        for subcategory in os.listdir(category_path):
            subcategory_path = os.path.join(category_path, subcategory)
            if not os.path.isdir(subcategory_path):
                continue

            await seed_subcategory(category, subcategory)

if __name__ == "__main__":
    asyncio.run(main())
