from bson import ObjectId
from datetime import datetime
from ....app.db.core.connection import get_saved_quizzes_collection

collection = get_saved_quizzes_collection()

async def save_quiz(user_id: str, title: str, quiz_data: dict):
    doc = {
        "user_id": user_id,
        "title": title,
        "quiz_data": quiz_data,
        "created_at": datetime.utcnow()
    }
    result = await collection.insert_one(doc)
    return str(result.inserted_id)

async def get_saved_quizzes(user_id: str):
    quizzes = await collection.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
    for q in quizzes:
        q["_id"] = str(q["_id"])
    return quizzes

async def delete_quiz(quiz_id: str):
    result = await collection.delete_one({"_id": ObjectId(quiz_id)})
    return result.deleted_count > 0
