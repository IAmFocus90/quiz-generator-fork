from datetime import datetime
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument

from ..models.quiz_models import QuizDocumentV2, QuizMetadataUpdateV2, QuizQuestionsUpdateV2


class QuizV2Repository:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def insert_quiz(self, quiz: QuizDocumentV2) -> QuizDocumentV2:
        payload = quiz.model_dump(by_alias=True)
        result = await self.collection.insert_one(payload)
        payload["_id"] = result.inserted_id
        return QuizDocumentV2(**payload)

    async def find_by_id(self, quiz_id: str) -> Optional[QuizDocumentV2]:
        try:
            document = await self.collection.find_one({"_id": ObjectId(quiz_id)})
        except InvalidId:
            return None
        return QuizDocumentV2(**document) if document else None

    async def update_metadata(
        self,
        quiz_id: str,
        update: QuizMetadataUpdateV2,
    ) -> Optional[QuizDocumentV2]:
        try:
            updated = await self.collection.find_one_and_update(
                {"_id": ObjectId(quiz_id)},
                {
                    "$set": {
                        **update.model_dump(exclude_unset=True),
                        "updated_at": datetime.utcnow(),
                    }
                },
                return_document=ReturnDocument.AFTER,
            )
        except InvalidId:
            return None
        return QuizDocumentV2(**updated) if updated else None

    async def update_questions(
        self,
        quiz_id: str,
        update: QuizQuestionsUpdateV2,
    ) -> Optional[QuizDocumentV2]:
        try:
            updated = await self.collection.find_one_and_update(
                {"_id": ObjectId(quiz_id)},
                {
                    "$set": {
                        "questions": [
                            question.model_dump() for question in update.questions
                        ],
                        "updated_at": datetime.utcnow(),
                    }
                },
                return_document=ReturnDocument.AFTER,
            )
        except InvalidId:
            return None
        return QuizDocumentV2(**updated) if updated else None

    async def soft_delete(self, quiz_id: str) -> Optional[QuizDocumentV2]:
        try:
            updated = await self.collection.find_one_and_update(
                {"_id": ObjectId(quiz_id), "status": {"$ne": "deleted"}},
                {
                    "$set": {
                        "status": "deleted",
                        "updated_at": datetime.utcnow(),
                        "deleted_at": datetime.utcnow(),
                    }
                },
                return_document=ReturnDocument.AFTER,
            )
        except InvalidId:
            return None
        return QuizDocumentV2(**updated) if updated else None
