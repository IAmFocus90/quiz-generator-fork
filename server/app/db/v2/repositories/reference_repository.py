from motor.motor_asyncio import AsyncIOMotorCollection

from ..models.reference_models import (
    FolderDocumentV2,
    FolderItemDocumentV2,
    QuizHistoryDocumentV2,
    SavedQuizDocumentV2,
)


class ReferenceV2Repository:
    def __init__(
        self,
        folders_collection: AsyncIOMotorCollection,
        folder_items_collection: AsyncIOMotorCollection,
        saved_quizzes_collection: AsyncIOMotorCollection,
        quiz_history_collection: AsyncIOMotorCollection,
    ):
        self.folders_collection = folders_collection
        self.folder_items_collection = folder_items_collection
        self.saved_quizzes_collection = saved_quizzes_collection
        self.quiz_history_collection = quiz_history_collection

    async def insert_folder(self, folder: FolderDocumentV2) -> FolderDocumentV2:
        payload = folder.model_dump(by_alias=True)
        result = await self.folders_collection.insert_one(payload)
        payload["_id"] = result.inserted_id
        return FolderDocumentV2(**payload)

    async def insert_folder_item(self, folder_item: FolderItemDocumentV2) -> FolderItemDocumentV2:
        payload = folder_item.model_dump(by_alias=True)
        result = await self.folder_items_collection.insert_one(payload)
        payload["_id"] = result.inserted_id
        return FolderItemDocumentV2(**payload)

    async def insert_saved_quiz(self, saved_quiz: SavedQuizDocumentV2) -> SavedQuizDocumentV2:
        payload = saved_quiz.model_dump(by_alias=True)
        result = await self.saved_quizzes_collection.insert_one(payload)
        payload["_id"] = result.inserted_id
        return SavedQuizDocumentV2(**payload)

    async def insert_quiz_history(self, quiz_history: QuizHistoryDocumentV2) -> QuizHistoryDocumentV2:
        payload = quiz_history.model_dump(by_alias=True)
        result = await self.quiz_history_collection.insert_one(payload)
        payload["_id"] = result.inserted_id
        return QuizHistoryDocumentV2(**payload)
