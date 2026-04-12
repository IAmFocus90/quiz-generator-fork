import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Literal, Optional

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from server.app.db.core.config import settings
from server.app.db.core.connection import (
    get_folder_items_v2_collection,
    get_folders_collection,
    get_folders_v2_collection,
    get_quiz_history_collection,
    get_quiz_history_v2_collection,
    get_quizzes_v2_collection,
    get_saved_quizzes_collection,
    get_saved_quizzes_v2_collection,
)
from server.app.db.v2.models.quiz_models import QuizDocumentV2
from server.app.db.v2.models.reference_models import (
    FolderDocumentV2,
    FolderItemDocumentV2,
    QuizHistoryDocumentV2,
    SavedQuizDocumentV2,
)
from server.app.db.v2.repositories.quiz_repository import QuizV2Repository
from server.app.db.v2.repositories.reference_repository import ReferenceV2Repository


logger = logging.getLogger(__name__)

ReadMode = Literal["legacy_only", "compare", "v2_only"]


class QuizUserLibraryReadService:
    def __init__(
        self,
        *,
        saved_quizzes_collection: Optional[AsyncIOMotorCollection] = None,
        quiz_history_collection: Optional[AsyncIOMotorCollection] = None,
        folders_collection: Optional[AsyncIOMotorCollection] = None,
        quiz_repository: Optional[QuizV2Repository] = None,
        reference_repository: Optional[ReferenceV2Repository] = None,
    ):
        self.saved_quizzes_collection = (
            saved_quizzes_collection
            if saved_quizzes_collection is not None
            else get_saved_quizzes_collection()
        )
        self.quiz_history_collection = (
            quiz_history_collection
            if quiz_history_collection is not None
            else get_quiz_history_collection()
        )
        self.folders_collection = (
            folders_collection if folders_collection is not None else get_folders_collection()
        )
        self.quiz_repository = (
            quiz_repository if quiz_repository is not None else QuizV2Repository(get_quizzes_v2_collection())
        )
        self.reference_repository = (
            reference_repository
            if reference_repository is not None
            else ReferenceV2Repository(
                get_folders_v2_collection(),
                get_folder_items_v2_collection(),
                get_saved_quizzes_v2_collection(),
                get_quiz_history_v2_collection(),
            )
        )

    def _log(self, event: str, **fields):
        if not settings.QUIZ_V2_STRUCTURED_LOGGING:
            return
        logger.info("%s | %s", event, fields)

    @staticmethod
    def _isoformat(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    @classmethod
    def _serialize_legacy_document(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: cls._serialize_legacy_document(val) for key, val in value.items()}
        if isinstance(value, list):
            return [cls._serialize_legacy_document(item) for item in value]
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    @staticmethod
    def _sort_by_created_desc(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(items, key=lambda item: item.get("created_at") or "", reverse=True)

    @staticmethod
    def _sort_folders(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(items, key=lambda item: (item.get("created_at") or "", item.get("_id") or ""))

    @staticmethod
    def _sort_folder_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def sort_key(item: dict[str, Any]):
            position = item.get("_position")
            if position is None:
                position = 10**9
            return (position, item.get("added_on") or item.get("created_at") or "", item.get("_id") or "")

        return sorted(items, key=sort_key)

    def _normalize_for_compare(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {key: self._normalize_for_compare(val) for key, val in value.items()}
        if isinstance(value, list):
            return [self._normalize_for_compare(item) for item in value]
        return value

    async def _read_with_mode(
        self,
        *,
        mode: ReadMode,
        operation: str,
        user_id: Optional[str],
        legacy_reader: Callable[[], Awaitable[Any]],
        v2_reader: Callable[[], Awaitable[Any]],
        compare_normalizer: Callable[[Any], Any],
    ):
        if mode == "legacy_only":
            data = await legacy_reader()
            self._log("quiz_read_legacy_served", operation=operation, user_id=user_id, read_mode=mode)
            return data

        if mode == "v2_only":
            data = await v2_reader()
            self._log("quiz_read_v2_served", operation=operation, user_id=user_id, read_mode=mode)
            return data

        self._log("quiz_read_compare_started", operation=operation, user_id=user_id, read_mode=mode)
        legacy_data = await legacy_reader()
        v2_data = await v2_reader()
        normalized_legacy = compare_normalizer(legacy_data)
        normalized_v2 = compare_normalizer(v2_data)
        if normalized_legacy == normalized_v2:
            self._log("quiz_read_compare_match", operation=operation, user_id=user_id, read_mode=mode)
        else:
            self._log(
                "quiz_read_compare_mismatch",
                operation=operation,
                user_id=user_id,
                read_mode=mode,
                legacy_shape=normalized_legacy,
                v2_shape=normalized_v2,
            )
        self._log("quiz_read_legacy_served", operation=operation, user_id=user_id, read_mode=mode)
        return legacy_data

    async def _get_quizzes_by_ids(self, quiz_ids: list[str]) -> dict[str, QuizDocumentV2]:
        quizzes = await self.quiz_repository.find_many_by_ids(quiz_ids)
        return {str(quiz.id): quiz for quiz in quizzes}

    @staticmethod
    def _serialize_saved_questions(quiz: QuizDocumentV2) -> list[dict[str, Any]]:
        return [
            {
                "question": question.question,
                "options": question.options,
                "question_type": quiz.quiz_type.value,
                "correct_answer": question.correct_answer,
            }
            for question in quiz.questions
        ]

    @staticmethod
    def _serialize_history_questions(quiz: QuizDocumentV2) -> list[dict[str, Any]]:
        return [
            {
                "question": question.question,
                "options": question.options,
                "answer": question.correct_answer,
                "question_type": quiz.quiz_type.value,
            }
            for question in quiz.questions
        ]

    async def _legacy_get_quiz_history(self, user_id: str, limit: int) -> list[dict[str, Any]]:
        documents = await self.quiz_history_collection.find({"user_id": user_id}).sort("created_at", -1).to_list(limit)
        return [self._serialize_legacy_document(document) for document in documents]

    async def _v2_get_quiz_history(self, user_id: str, limit: int) -> list[dict[str, Any]]:
        references = await self.reference_repository.list_quiz_history_for_user(user_id)
        references = sorted(references, key=lambda reference: reference.created_at, reverse=True)[:limit]
        quizzes_by_id = await self._get_quizzes_by_ids([reference.quiz_id for reference in references])
        payload: list[dict[str, Any]] = []
        for reference in references:
            quiz = quizzes_by_id.get(reference.quiz_id)
            if quiz is None:
                continue
            payload.append(
                {
                    "_id": reference.legacy_history_id or str(reference.id),
                    "user_id": reference.user_id,
                    "quiz_id": quiz.legacy_quiz_id,
                    "canonical_quiz_id": str(quiz.id),
                    "quiz_name": quiz.title,
                    "question_type": quiz.quiz_type.value,
                    "profession": reference.metadata.get("topic") or quiz.title,
                    "difficulty_level": reference.metadata.get("difficulty_level"),
                    "audience_type": reference.metadata.get("audience_type"),
                    "questions": self._serialize_history_questions(quiz),
                    "created_at": self._isoformat(reference.created_at),
                }
            )
        return payload

    @staticmethod
    def _normalize_history_compare(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = [
            {
                "_id": item.get("_id"),
                "created_at": item.get("created_at"),
                "question_count": len(item.get("questions", [])),
                "questions": [question.get("question") for question in item.get("questions", [])],
            }
            for item in items
        ]
        return sorted(normalized, key=lambda item: item["_id"])

    async def get_quiz_history_for_user(self, user_id: str, limit: int = 100) -> list[dict[str, Any]]:
        mode = settings.QUIZ_V2_HISTORY_READ_MODE
        return await self._read_with_mode(
            mode=mode,
            operation="quiz_history_list",
            user_id=user_id,
            legacy_reader=lambda: self._legacy_get_quiz_history(user_id, limit),
            v2_reader=lambda: self._v2_get_quiz_history(user_id, limit),
            compare_normalizer=self._normalize_history_compare,
        )

    async def _legacy_list_saved_quizzes(self, user_id: str, limit: int) -> list[dict[str, Any]]:
        documents = await self.saved_quizzes_collection.find({"user_id": user_id}).sort("created_at", -1).to_list(limit)
        return [self._serialize_legacy_document(document) for document in documents]

    async def _legacy_get_saved_quiz(self, saved_quiz_id: str, user_id: str) -> Optional[dict[str, Any]]:
        try:
            object_id = ObjectId(saved_quiz_id)
        except InvalidId:
            return None
        document = await self.saved_quizzes_collection.find_one({"_id": object_id, "user_id": user_id})
        return self._serialize_legacy_document(document) if document else None

    def _build_saved_payload(self, reference: SavedQuizDocumentV2, quiz: QuizDocumentV2) -> dict[str, Any]:
        return {
            "_id": reference.legacy_saved_quiz_id or str(reference.id),
            "user_id": reference.user_id,
            "quiz_id": quiz.legacy_quiz_id,
            "canonical_quiz_id": str(quiz.id),
            "title": reference.display_title or quiz.title,
            "question_type": quiz.quiz_type.value,
            "is_deleted": False,
            "questions": self._serialize_saved_questions(quiz),
            "created_at": self._isoformat(reference.saved_at),
        }

    async def _v2_list_saved_quizzes(self, user_id: str, limit: int) -> list[dict[str, Any]]:
        references = await self.reference_repository.list_saved_quizzes_for_user(user_id)
        references = sorted(references, key=lambda reference: reference.saved_at, reverse=True)[:limit]
        quizzes_by_id = await self._get_quizzes_by_ids([reference.quiz_id for reference in references])
        payload: list[dict[str, Any]] = []
        for reference in references:
            quiz = quizzes_by_id.get(reference.quiz_id)
            if quiz is None:
                continue
            payload.append(self._build_saved_payload(reference, quiz))
        return payload

    async def _v2_get_saved_quiz(self, saved_quiz_id: str, user_id: str) -> Optional[dict[str, Any]]:
        reference = await self.reference_repository.get_saved_quiz_by_legacy_id(saved_quiz_id, user_id=user_id)
        if reference is None:
            return None
        quiz = await self.quiz_repository.find_by_id(reference.quiz_id)
        if quiz is None:
            return None
        return self._build_saved_payload(reference, quiz)

    @staticmethod
    def _normalize_saved_compare(items: Any) -> Any:
        if items is None:
            return None
        if isinstance(items, dict):
            items = [items]
            unwrap = True
        else:
            unwrap = False
        normalized = [
            {
                "_id": item.get("_id"),
                "title": item.get("title"),
                "created_at": item.get("created_at"),
                "question_type": item.get("question_type"),
                "question_count": len(item.get("questions", [])),
                "questions": [question.get("question") for question in item.get("questions", [])],
            }
            for item in items
        ]
        normalized = sorted(normalized, key=lambda item: item["_id"])
        return normalized[0] if unwrap else normalized

    async def get_saved_quizzes_for_user(self, user_id: str, limit: int = 100) -> list[dict[str, Any]]:
        mode = settings.QUIZ_V2_SAVED_READ_MODE
        return await self._read_with_mode(
            mode=mode,
            operation="saved_quiz_list",
            user_id=user_id,
            legacy_reader=lambda: self._legacy_list_saved_quizzes(user_id, limit),
            v2_reader=lambda: self._v2_list_saved_quizzes(user_id, limit),
            compare_normalizer=self._normalize_saved_compare,
        )

    async def get_saved_quiz_by_id(self, saved_quiz_id: str, user_id: str) -> Optional[dict[str, Any]]:
        mode = settings.QUIZ_V2_SAVED_READ_MODE
        return await self._read_with_mode(
            mode=mode,
            operation="saved_quiz_detail",
            user_id=user_id,
            legacy_reader=lambda: self._legacy_get_saved_quiz(saved_quiz_id, user_id),
            v2_reader=lambda: self._v2_get_saved_quiz(saved_quiz_id, user_id),
            compare_normalizer=self._normalize_saved_compare,
        )

    async def _legacy_list_folders(self, user_id: str) -> list[dict[str, Any]]:
        documents = await self.folders_collection.find({"user_id": user_id}).to_list(length=500)
        return self._sort_folders([self._serialize_legacy_document(document) for document in documents])

    async def _legacy_get_folder(self, folder_id: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
        try:
            object_id = ObjectId(folder_id)
        except InvalidId:
            return None, None
        document = await self.folders_collection.find_one({"_id": object_id})
        if not document:
            return None, None
        folder = self._serialize_legacy_document(document)
        return folder, folder.get("user_id")

    def _build_folder_item_payload(
        self,
        *,
        item: FolderItemDocumentV2,
        quiz: QuizDocumentV2,
    ) -> dict[str, Any]:
        questions = self._serialize_saved_questions(quiz)
        return {
            "_id": item.legacy_folder_item_id or str(item.id),
            "quiz_id": quiz.legacy_quiz_id,
            "canonical_quiz_id": str(quiz.id),
            "title": item.display_title or quiz.title,
            "question_type": quiz.quiz_type.value,
            "questions": questions,
            "created_at": self._isoformat(item.created_at),
            "added_on": self._isoformat(item.created_at),
            "_position": item.position,
            "quiz_data": {
                "_id": item.legacy_folder_item_id or str(item.id),
                "quiz_id": quiz.legacy_quiz_id,
                "canonical_quiz_id": str(quiz.id),
                "title": item.display_title or quiz.title,
                "question_type": quiz.quiz_type.value,
                "questions": questions,
                "created_at": self._isoformat(quiz.created_at),
            },
        }

    async def _v2_list_folders(self, user_id: str) -> list[dict[str, Any]]:
        folders = await self.reference_repository.list_folders_for_user(user_id)
        folders = sorted(folders, key=lambda folder: (folder.created_at, folder.legacy_folder_id or str(folder.id)))
        folder_payloads: list[dict[str, Any]] = []
        for folder in folders:
            items = await self.reference_repository.list_folder_items_for_folder(str(folder.id))
            folder_payloads.append(
                {
                    "_id": folder.legacy_folder_id or str(folder.id),
                    "user_id": folder.user_id,
                    "name": folder.name,
                    "created_at": self._isoformat(folder.created_at),
                    "updated_at": self._isoformat(folder.updated_at),
                    "quizzes": [{"_id": item.legacy_folder_item_id or str(item.id)} for item in items],
                }
            )
        return folder_payloads

    async def _v2_get_folder(self, folder_id: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
        folder = await self.reference_repository.get_folder_by_legacy_id(folder_id)
        if folder is None:
            return None, None
        items = await self.reference_repository.list_folder_items_for_folder(str(folder.id))
        quiz_map = await self._get_quizzes_by_ids([item.quiz_id for item in items])
        payload_items: list[dict[str, Any]] = []
        for item in items:
            quiz = quiz_map.get(item.quiz_id)
            if quiz is None:
                continue
            payload_items.append(self._build_folder_item_payload(item=item, quiz=quiz))
        payload_items = self._sort_folder_items(payload_items)
        for payload_item in payload_items:
            payload_item.pop("_position", None)
        return (
            {
                "_id": folder.legacy_folder_id or str(folder.id),
                "user_id": folder.user_id,
                "name": folder.name,
                "created_at": self._isoformat(folder.created_at),
                "updated_at": self._isoformat(folder.updated_at),
                "quizzes": payload_items,
            },
            folder.user_id,
        )

    @staticmethod
    def _normalize_folder_compare(items: Any) -> Any:
        if items is None:
            return None
        if isinstance(items, dict):
            quizzes = items.get("quizzes", [])
            return {
                "_id": items.get("_id"),
                "name": items.get("name"),
                "quiz_ids": [quiz.get("_id") for quiz in quizzes],
                "quiz_titles": [quiz.get("title") for quiz in quizzes],
                "question_counts": [
                    len(quiz.get("questions") or quiz.get("quiz_data", {}).get("questions", []))
                    for quiz in quizzes
                ],
            }
        normalized = [
            {
                "_id": item.get("_id"),
                "name": item.get("name"),
                "quiz_count": len(item.get("quizzes", [])),
            }
            for item in items
        ]
        return sorted(normalized, key=lambda item: item["_id"])

    async def get_user_folders(self, user_id: str) -> list[dict[str, Any]]:
        mode = settings.QUIZ_V2_FOLDER_READ_MODE
        return await self._read_with_mode(
            mode=mode,
            operation="folder_list",
            user_id=user_id,
            legacy_reader=lambda: self._legacy_list_folders(user_id),
            v2_reader=lambda: self._v2_list_folders(user_id),
            compare_normalizer=self._normalize_folder_compare,
        )

    async def get_folder_by_id(self, folder_id: str, user_id: str) -> Optional[dict[str, Any]]:
        mode = settings.QUIZ_V2_FOLDER_READ_MODE

        async def legacy_reader():
            folder, owner_id = await self._legacy_get_folder(folder_id)
            if folder is None:
                return None
            if owner_id != user_id:
                raise PermissionError("Unauthorized access to folder")
            return folder

        async def v2_reader():
            folder, owner_id = await self._v2_get_folder(folder_id)
            if folder is None:
                return None
            if owner_id != user_id:
                raise PermissionError("Unauthorized access to folder")
            return folder

        return await self._read_with_mode(
            mode=mode,
            operation="folder_detail",
            user_id=user_id,
            legacy_reader=legacy_reader,
            v2_reader=v2_reader,
            compare_normalizer=self._normalize_folder_compare,
        )
