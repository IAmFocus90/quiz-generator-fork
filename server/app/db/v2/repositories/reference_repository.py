from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument

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

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

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

    async def upsert_folder_by_legacy_id(self, folder: FolderDocumentV2) -> FolderDocumentV2:
        payload = folder.model_dump(by_alias=True)
        payload.pop("_id", None)
        updated = await self.folders_collection.find_one_and_update(
            {"legacy_folder_id": folder.legacy_folder_id},
            {"$set": payload},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return FolderDocumentV2(**updated)

    async def get_folder_by_legacy_id(self, legacy_folder_id: str) -> FolderDocumentV2 | None:
        document = await self.folders_collection.find_one({"legacy_folder_id": legacy_folder_id})
        return FolderDocumentV2(**document) if document else None

    async def delete_folder_by_legacy_id(self, legacy_folder_id: str):
        folder = await self.get_folder_by_legacy_id(legacy_folder_id)
        if folder:
            await self.folder_items_collection.delete_many({"folder_id": str(folder.id)})
        await self.folders_collection.delete_one({"legacy_folder_id": legacy_folder_id})

    async def upsert_folder_item_by_legacy_id(self, folder_item: FolderItemDocumentV2) -> FolderItemDocumentV2:
        payload = folder_item.model_dump(by_alias=True)
        payload.pop("_id", None)
        updated = await self.folder_items_collection.find_one_and_update(
            {"legacy_folder_item_id": folder_item.legacy_folder_item_id},
            {"$set": payload},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return FolderItemDocumentV2(**updated)

    async def get_folder_item_by_legacy_id(self, legacy_folder_item_id: str) -> FolderItemDocumentV2 | None:
        document = await self.folder_items_collection.find_one(
            {"legacy_folder_item_id": legacy_folder_item_id}
        )
        return FolderItemDocumentV2(**document) if document else None

    async def delete_folder_item_by_legacy_id(self, legacy_folder_item_id: str):
        await self.folder_items_collection.delete_one({"legacy_folder_item_id": legacy_folder_item_id})

    async def upsert_saved_quiz(self, saved_quiz: SavedQuizDocumentV2) -> SavedQuizDocumentV2:
        payload = saved_quiz.model_dump(by_alias=True)
        payload.pop("_id", None)
        saved_at = payload.pop("saved_at")
        legacy_match = None
        if saved_quiz.legacy_saved_quiz_id:
            legacy_match = await self.saved_quizzes_collection.find_one(
                {"legacy_saved_quiz_id": saved_quiz.legacy_saved_quiz_id}
            )
        target_match = await self.saved_quizzes_collection.find_one(
            {"user_id": saved_quiz.user_id, "quiz_id": saved_quiz.quiz_id}
        )

        if legacy_match and target_match and legacy_match["_id"] != target_match["_id"]:
            merged_saved_at = min(
                self._normalize_datetime(saved_at),
                self._normalize_datetime(legacy_match.get("saved_at", saved_at)),
                self._normalize_datetime(target_match.get("saved_at", saved_at)),
            )
            updated = await self.saved_quizzes_collection.find_one_and_update(
                {"_id": target_match["_id"]},
                {
                    "$set": {
                        **payload,
                        "saved_at": merged_saved_at,
                    }
                },
                return_document=ReturnDocument.AFTER,
            )
            await self.saved_quizzes_collection.delete_one({"_id": legacy_match["_id"]})
            return SavedQuizDocumentV2(**updated)

        if legacy_match is not None:
            filter_query = {"_id": legacy_match["_id"]}
        elif target_match is not None:
            filter_query = {"_id": target_match["_id"]}
        else:
            filter_query = (
                {"legacy_saved_quiz_id": saved_quiz.legacy_saved_quiz_id}
                if saved_quiz.legacy_saved_quiz_id
                else {"user_id": saved_quiz.user_id, "quiz_id": saved_quiz.quiz_id}
            )
        updated = await self.saved_quizzes_collection.find_one_and_update(
            filter_query,
            {"$set": payload, "$setOnInsert": {"saved_at": saved_at}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return SavedQuizDocumentV2(**updated)

    async def upsert_quiz_history(self, quiz_history: QuizHistoryDocumentV2) -> QuizHistoryDocumentV2:
        payload = quiz_history.model_dump(by_alias=True)
        payload.pop("_id", None)
        created_at = payload.pop("created_at")
        updated = await self.quiz_history_collection.find_one_and_update(
            {"legacy_history_id": quiz_history.legacy_history_id},
            {"$set": payload, "$setOnInsert": {"created_at": created_at}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return QuizHistoryDocumentV2(**updated)
