import logging
from typing import Any, Optional

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from server.app.db.core.config import settings
from server.app.db.core.connection import (
    get_ai_generated_quizzes_collection,
    get_quizzes_collection,
    get_quizzes_v2_collection,
    get_saved_quizzes_collection,
    get_saved_quizzes_v2_collection,
    get_folder_items_v2_collection,
    get_folders_v2_collection,
    get_quiz_history_v2_collection,
)
from server.app.db.services.quiz_user_library_read_service import ReadMode
from server.app.db.v2.models.quiz_models import QuizDocumentV2
from server.app.db.v2.repositories.quiz_repository import QuizV2Repository
from server.app.db.v2.repositories.reference_repository import ReferenceV2Repository


logger = logging.getLogger(__name__)


def build_default_description(topic: str) -> str:
    return f"A quiz to test your knowledge on {topic}"


class SharedQuizReadService:
    def __init__(
        self,
        *,
        quizzes_collection: Optional[AsyncIOMotorCollection] = None,
        ai_generated_quizzes_collection: Optional[AsyncIOMotorCollection] = None,
        saved_quizzes_collection: Optional[AsyncIOMotorCollection] = None,
        quiz_repository: Optional[QuizV2Repository] = None,
        reference_repository: Optional[ReferenceV2Repository] = None,
    ):
        self.quizzes_collection = (
            quizzes_collection if quizzes_collection is not None else get_quizzes_collection()
        )
        self.ai_generated_quizzes_collection = (
            ai_generated_quizzes_collection
            if ai_generated_quizzes_collection is not None
            else get_ai_generated_quizzes_collection()
        )
        self.saved_quizzes_collection = (
            saved_quizzes_collection
            if saved_quizzes_collection is not None
            else get_saved_quizzes_collection()
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
    def _normalize_legacy_quiz(
        quiz_doc: dict[str, Any],
        quiz_id: str,
        source: str,
    ) -> dict[str, Any]:
        if source == "quizzes":
            title = quiz_doc.get("title") or "General Knowledge"
            description = quiz_doc.get("description") or build_default_description(title)
            quiz_type = quiz_doc.get("quiz_type") or "multichoice"
        elif source == "ai_generated_quizzes":
            profession = quiz_doc.get("profession") or "General Knowledge"
            title = profession
            description = quiz_doc.get("description") or build_default_description(profession)
            quiz_type = quiz_doc.get("question_type") or "multichoice"
        elif source == "saved_quizzes":
            title = quiz_doc.get("title") or "General Knowledge"
            topic = quiz_doc.get("profession") or title
            description = quiz_doc.get("description") or build_default_description(topic)
            quiz_type = quiz_doc.get("question_type") or "multichoice"
        else:
            raise ValueError(f"Unsupported shared quiz source: {source}")

        return {
            "id": quiz_id,
            "title": title,
            "description": description,
            "quiz_type": quiz_type,
            "questions": quiz_doc.get("questions", []),
        }

    @staticmethod
    def _normalize_v2_quiz(quiz_doc: QuizDocumentV2, requested_quiz_id: str) -> dict[str, Any]:
        topic = quiz_doc.title or "General Knowledge"
        return {
            "id": str(quiz_doc.id),
            "legacy_quiz_id": quiz_doc.legacy_quiz_id,
            "requested_quiz_id": requested_quiz_id,
            "title": quiz_doc.title,
            "description": quiz_doc.description or build_default_description(topic),
            "quiz_type": quiz_doc.quiz_type.value,
            "questions": [
                {
                    "question": question.question,
                    "options": question.options,
                    "correct_answer": question.correct_answer,
                }
                for question in quiz_doc.questions
            ],
        }

    async def _legacy_resolve(self, quiz_id: str) -> Optional[dict[str, Any]]:
        try:
            object_id = ObjectId(quiz_id)
        except InvalidId:
            return None

        regular_quiz = await self.quizzes_collection.find_one({"_id": object_id}, projection={"_id": 0})
        if regular_quiz:
            return self._normalize_legacy_quiz(regular_quiz, quiz_id, "quizzes")

        ai_quiz = await self.ai_generated_quizzes_collection.find_one({"_id": object_id}, projection={"_id": 0})
        if ai_quiz:
            return self._normalize_legacy_quiz(ai_quiz, quiz_id, "ai_generated_quizzes")

        saved_quiz = await self.saved_quizzes_collection.find_one({"_id": object_id}, projection={"_id": 0})
        if saved_quiz:
            return self._normalize_legacy_quiz(saved_quiz, quiz_id, "saved_quizzes")
        return None

    async def _v2_resolve(self, quiz_id: str) -> Optional[dict[str, Any]]:
        quiz_doc = await self.quiz_repository.find_by_id(quiz_id)
        if quiz_doc:
            return self._normalize_v2_quiz(quiz_doc, quiz_id)

        quiz_doc = await self.quiz_repository.find_by_legacy_mapping("quizzes", quiz_id)
        if quiz_doc:
            return self._normalize_v2_quiz(quiz_doc, quiz_id)

        quiz_doc = await self.quiz_repository.find_by_legacy_mapping("ai_generated_quizzes", quiz_id)
        if quiz_doc:
            return self._normalize_v2_quiz(quiz_doc, quiz_id)

        saved_reference = await self.reference_repository.get_saved_quiz_by_legacy_id(quiz_id)
        if saved_reference:
            quiz_doc = await self.quiz_repository.find_by_id(saved_reference.quiz_id)
            if quiz_doc:
                return self._normalize_v2_quiz(quiz_doc, quiz_id)
        return None

    @staticmethod
    def _normalize_for_compare(payload: Optional[dict[str, Any]]) -> Any:
        if payload is None:
            return None
        return {
            "title": payload.get("title"),
            "description": payload.get("description"),
            "quiz_type": payload.get("quiz_type"),
            "question_count": len(payload.get("questions", [])),
            "questions": [question.get("question") for question in payload.get("questions", [])],
        }

    async def resolve_shared_quiz(self, quiz_id: str) -> Optional[dict[str, Any]]:
        mode: ReadMode = settings.QUIZ_V2_SHARE_READ_MODE

        if mode == "legacy_only":
            payload = await self._legacy_resolve(quiz_id)
            self._log("quiz_read_legacy_served", operation="shared_quiz_detail", read_mode=mode, quiz_id=quiz_id)
            return payload

        if mode == "v2_only":
            payload = await self._v2_resolve(quiz_id)
            self._log("quiz_read_v2_served", operation="shared_quiz_detail", read_mode=mode, quiz_id=quiz_id)
            return payload

        self._log("quiz_read_compare_started", operation="shared_quiz_detail", read_mode=mode, quiz_id=quiz_id)
        legacy_payload = await self._legacy_resolve(quiz_id)
        v2_payload = await self._v2_resolve(quiz_id)
        if self._normalize_for_compare(legacy_payload) == self._normalize_for_compare(v2_payload):
            self._log("quiz_read_compare_match", operation="shared_quiz_detail", read_mode=mode, quiz_id=quiz_id)
        else:
            self._log(
                "quiz_read_compare_mismatch",
                operation="shared_quiz_detail",
                read_mode=mode,
                quiz_id=quiz_id,
                legacy_shape=self._normalize_for_compare(legacy_payload),
                v2_shape=self._normalize_for_compare(v2_payload),
            )
        self._log("quiz_read_legacy_served", operation="shared_quiz_detail", read_mode=mode, quiz_id=quiz_id)
        return legacy_payload
