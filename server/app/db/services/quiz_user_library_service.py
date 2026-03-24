from datetime import datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from server.app.db.core.connection import (
    get_quiz_history_collection,
    get_saved_quizzes_collection,
)
from server.app.db.crud.quiz_write_service import CanonicalQuizWriteService
from server.app.db.schemas.quiz_management_schemas import (
    QuizHistoryDetailResponse,
    QuizHistoryQuestionResponse,
    SavedQuizResponse,
)
from server.app.db.services.quiz_dual_write_service import QuizDualWriteService
from server.app.db.v2.repositories.reference_repository import ReferenceV2Repository


class QuizUserLibraryService:
    def __init__(
        self,
        *,
        canonical_service: CanonicalQuizWriteService | None = None,
        reference_repository: ReferenceV2Repository | None = None,
        dual_write_service: QuizDualWriteService | None = None,
    ):
        self.canonical_service = canonical_service or CanonicalQuizWriteService()
        self.dual_write_service = dual_write_service or QuizDualWriteService()
        self.reference_repository = (
            reference_repository or self.dual_write_service.reference_repository
        )
        self.legacy_history_collection = get_quiz_history_collection()
        self.legacy_saved_quizzes_collection = get_saved_quizzes_collection()

    @staticmethod
    def _normalize_datetime(value: Any) -> datetime | None:
        return value if isinstance(value, datetime) else None

    async def get_quiz_history_detail(
        self,
        *,
        user_id: str,
        history_id: str,
    ) -> QuizHistoryDetailResponse | None:
        history_ref = await self.reference_repository.get_quiz_history_for_user(
            user_id,
            history_id,
        )
        if not history_ref:
            return None

        canonical_quiz = await self.canonical_service.get_quiz_v2_by_id(history_ref.quiz_id)
        metadata = history_ref.metadata or {}
        legacy_history_id = history_ref.legacy_history_id or str(history_ref.id)

        legacy_history = None
        if metadata.get("custom_instruction") is None and history_ref.legacy_history_id:
            try:
                legacy_history = await self.legacy_history_collection.find_one(
                    {
                        "_id": ObjectId(history_ref.legacy_history_id),
                        "user_id": user_id,
                    }
                )
            except InvalidId:
                legacy_history = None

        questions = []
        if canonical_quiz:
            questions = [
                QuizHistoryQuestionResponse(
                    question=question.question,
                    options=question.options,
                    answer=question.correct_answer,
                )
                for question in canonical_quiz.questions
            ]
        elif legacy_history:
            questions = [
                QuizHistoryQuestionResponse(
                    question=question.get("question", ""),
                    options=question.get("options"),
                    answer=question.get("answer") or question.get("correct_answer", ""),
                )
                for question in legacy_history.get("questions", [])
            ]

        return QuizHistoryDetailResponse(
            id=legacy_history_id,
            created_at=self._normalize_datetime(history_ref.created_at),
            quiz_name=metadata.get("quiz_name"),
            question_type=(
                (canonical_quiz.quiz_type if canonical_quiz else None)
                or (legacy_history.get("question_type") if legacy_history else None)
                or "multichoice"
            ),
            difficulty_level=metadata.get("difficulty_level")
            or (legacy_history.get("difficulty_level") if legacy_history else None),
            profession=metadata.get("topic")
            or (legacy_history.get("profession") if legacy_history else None),
            audience_type=metadata.get("audience_type")
            or (legacy_history.get("audience_type") if legacy_history else None),
            custom_instruction=metadata.get("custom_instruction")
            or (legacy_history.get("custom_instruction") if legacy_history else None),
            questions=questions,
        )

    async def delete_quiz_history_entry(
        self,
        *,
        user_id: str,
        history_id: str,
    ) -> bool:
        history_ref = await self.reference_repository.get_quiz_history_for_user(
            user_id,
            history_id,
        )
        if not history_ref:
            return False

        deleted = await self.reference_repository.delete_quiz_history_for_user(
            user_id,
            history_id,
        )
        if not deleted:
            return False

        if history_ref.legacy_history_id:
            try:
                await self.legacy_history_collection.delete_one(
                    {
                        "_id": ObjectId(history_ref.legacy_history_id),
                        "user_id": user_id,
                    }
                )
            except InvalidId:
                pass
        return True

    async def rename_saved_quiz(
        self,
        *,
        user_id: str,
        saved_quiz_id: str,
        title: str,
    ) -> SavedQuizResponse | None:
        saved_ref = await self.reference_repository.update_saved_quiz_display_title(
            user_id,
            saved_quiz_id,
            title,
        )
        if not saved_ref:
            return None

        legacy_saved_quiz_id = saved_ref.legacy_saved_quiz_id or saved_quiz_id
        legacy_saved_quiz = None
        try:
            legacy_saved_quiz = await self.legacy_saved_quizzes_collection.find_one_and_update(
                {
                    "_id": ObjectId(legacy_saved_quiz_id),
                    "user_id": user_id,
                },
                {"$set": {"title": title, "updated_at": datetime.utcnow()}},
                return_document=ReturnDocument.AFTER,
            )
        except InvalidId:
            legacy_saved_quiz = None

        return SavedQuizResponse(
            id=legacy_saved_quiz_id,
            quiz_id=saved_ref.quiz_id,
            title=title,
            created_at=self._normalize_datetime(saved_ref.saved_at)
            or (legacy_saved_quiz.get("created_at") if legacy_saved_quiz else None),
            question_type=legacy_saved_quiz.get("question_type") if legacy_saved_quiz else None,
        )
