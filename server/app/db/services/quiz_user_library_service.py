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

    async def _get_legacy_quiz_history(
        self,
        *,
        user_id: str,
        history_id: str,
    ) -> dict[str, Any] | None:
        try:
            object_id = ObjectId(history_id)
        except InvalidId:
            return None
        return await self.legacy_history_collection.find_one(
            {"_id": object_id, "user_id": user_id}
        )

    async def _get_legacy_saved_quiz(
        self,
        *,
        user_id: str,
        saved_quiz_id: str,
    ) -> dict[str, Any] | None:
        try:
            object_id = ObjectId(saved_quiz_id)
        except InvalidId:
            return None
        return await self.legacy_saved_quizzes_collection.find_one(
            {"_id": object_id, "user_id": user_id}
        )

    async def list_quiz_history_items(
        self,
        *,
        user_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        history_refs = await self.reference_repository.list_quiz_history_for_user(
            user_id,
            limit=limit,
        )
        legacy_history_docs = await self.legacy_history_collection.find({"user_id": user_id}).sort(
            "created_at", -1
        ).to_list(length=limit)
        legacy_by_id = {str(doc["_id"]): doc for doc in legacy_history_docs}
        items: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for history_ref in history_refs:
            legacy_id = history_ref.legacy_history_id or str(history_ref.id)
            legacy_doc = legacy_by_id.get(legacy_id)
            canonical_quiz = await self.canonical_service.get_quiz_v2_by_id(history_ref.quiz_id)
            metadata = history_ref.metadata or {}
            item = {
                "_id": legacy_id,
                "created_at": (
                    self._normalize_datetime(history_ref.created_at)
                    or (legacy_doc.get("created_at") if legacy_doc else None)
                ),
                "quiz_name": metadata.get("quiz_name")
                or (canonical_quiz.title if canonical_quiz else None)
                or (legacy_doc.get("quiz_name") if legacy_doc else None),
                "question_type": (
                    (canonical_quiz.quiz_type if canonical_quiz else None)
                    or (legacy_doc.get("question_type") if legacy_doc else None)
                    or "multichoice"
                ),
                "difficulty_level": metadata.get("difficulty_level")
                or (legacy_doc.get("difficulty_level") if legacy_doc else None),
                "profession": metadata.get("topic")
                or (legacy_doc.get("profession") if legacy_doc else None),
                "audience_type": metadata.get("audience_type")
                or (legacy_doc.get("audience_type") if legacy_doc else None),
                "custom_instruction": metadata.get("custom_instruction")
                or (legacy_doc.get("custom_instruction") if legacy_doc else None),
                "questions": [],
            }
            if canonical_quiz:
                item["questions"] = [
                    {
                        "question": question.question,
                        "options": question.options,
                        "answer": question.correct_answer,
                    }
                    for question in canonical_quiz.questions
                ]
            elif legacy_doc:
                item["questions"] = legacy_doc.get("questions", [])

            if isinstance(item["created_at"], datetime):
                item["created_at"] = item["created_at"].isoformat()

            items.append(item)
            seen_ids.add(legacy_id)

        for legacy_doc in legacy_history_docs:
            legacy_id = str(legacy_doc["_id"])
            if legacy_id in seen_ids:
                continue
            item = dict(legacy_doc)
            item["_id"] = legacy_id
            if isinstance(item.get("created_at"), datetime):
                item["created_at"] = item["created_at"].isoformat()
            items.append(item)

        items.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return items[:limit]

    async def list_saved_quizzes(
        self,
        *,
        user_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        saved_refs = await self.reference_repository.list_saved_quizzes_for_user(
            user_id,
            limit=limit,
        )
        legacy_saved_docs = await self.legacy_saved_quizzes_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).to_list(length=limit)
        legacy_by_id = {str(doc["_id"]): doc for doc in legacy_saved_docs}
        items: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for saved_ref in saved_refs:
            legacy_id = saved_ref.legacy_saved_quiz_id or str(saved_ref.id)
            legacy_doc = legacy_by_id.get(legacy_id)
            canonical_quiz = await self.canonical_service.get_quiz_v2_by_id(saved_ref.quiz_id)
            item = {
                "_id": legacy_id,
                "quiz_id": saved_ref.quiz_id,
                "title": saved_ref.display_title
                or (legacy_doc.get("title") if legacy_doc else None)
                or (canonical_quiz.title if canonical_quiz else "Saved Quiz"),
                "question_type": (
                    (legacy_doc.get("question_type") if legacy_doc else None)
                    or (canonical_quiz.quiz_type if canonical_quiz else None)
                ),
                "created_at": (
                    self._normalize_datetime(saved_ref.saved_at)
                    or (legacy_doc.get("created_at") if legacy_doc else None)
                ),
                "questions": [],
            }
            if legacy_doc and legacy_doc.get("questions"):
                item["questions"] = legacy_doc["questions"]
            elif canonical_quiz:
                item["questions"] = [
                    {
                        "question": question.question,
                        "options": question.options,
                        "correct_answer": question.correct_answer,
                    }
                    for question in canonical_quiz.questions
                ]

            if isinstance(item["created_at"], datetime):
                item["created_at"] = item["created_at"].isoformat()

            items.append(item)
            seen_ids.add(legacy_id)

        for legacy_doc in legacy_saved_docs:
            legacy_id = str(legacy_doc["_id"])
            if legacy_id in seen_ids:
                continue
            item = dict(legacy_doc)
            item["_id"] = legacy_id
            if isinstance(item.get("created_at"), datetime):
                item["created_at"] = item["created_at"].isoformat()
            items.append(item)

        items.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return items[:limit]

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
        legacy_history = None
        canonical_quiz = None
        metadata: dict[str, Any] = {}
        legacy_history_id = history_id

        if history_ref:
            canonical_quiz = await self.canonical_service.get_quiz_v2_by_id(history_ref.quiz_id)
            metadata = history_ref.metadata or {}
            legacy_history_id = history_ref.legacy_history_id or str(history_ref.id)

            if metadata.get("custom_instruction") is None and history_ref.legacy_history_id:
                legacy_history = await self._get_legacy_quiz_history(
                    user_id=user_id,
                    history_id=history_ref.legacy_history_id,
                )
        else:
            legacy_history = await self._get_legacy_quiz_history(
                user_id=user_id,
                history_id=history_id,
            )
            if not legacy_history:
                return None

            legacy_history_id = str(legacy_history["_id"])
            metadata = {
                "quiz_name": legacy_history.get("quiz_name"),
                "difficulty_level": legacy_history.get("difficulty_level"),
                "topic": legacy_history.get("profession"),
                "audience_type": legacy_history.get("audience_type"),
                "custom_instruction": legacy_history.get("custom_instruction"),
            }
            canonical_quiz_id = legacy_history.get("canonical_quiz_id")
            if canonical_quiz_id:
                canonical_quiz = await self.canonical_service.get_quiz_v2_by_id(
                    canonical_quiz_id
                )

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
            created_at=(
                self._normalize_datetime(history_ref.created_at) if history_ref else None
            )
            or (legacy_history.get("created_at") if legacy_history else None),
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
        if history_ref:
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

        legacy_history = await self._get_legacy_quiz_history(
            user_id=user_id,
            history_id=history_id,
        )
        if not legacy_history:
            return False

        result = await self.legacy_history_collection.delete_one(
            {"_id": legacy_history["_id"], "user_id": user_id}
        )
        if result.deleted_count:
            await self.reference_repository.delete_quiz_history_by_legacy_id(
                str(legacy_history["_id"])
            )
        return result.deleted_count > 0

    async def get_saved_quiz(
        self,
        *,
        user_id: str,
        saved_quiz_id: str,
    ) -> dict[str, Any] | None:
        saved_ref = await self.reference_repository.get_saved_quiz_for_user(
            user_id,
            saved_quiz_id,
        )
        legacy_saved_quiz = None
        canonical_quiz = None
        result_id = saved_quiz_id

        if saved_ref:
            result_id = saved_ref.legacy_saved_quiz_id or str(saved_ref.id)
            canonical_quiz = await self.canonical_service.get_quiz_v2_by_id(saved_ref.quiz_id)
            if saved_ref.legacy_saved_quiz_id:
                legacy_saved_quiz = await self._get_legacy_saved_quiz(
                    user_id=user_id,
                    saved_quiz_id=saved_ref.legacy_saved_quiz_id,
                )
        else:
            legacy_saved_quiz = await self._get_legacy_saved_quiz(
                user_id=user_id,
                saved_quiz_id=saved_quiz_id,
            )
            if not legacy_saved_quiz:
                return None
            result_id = str(legacy_saved_quiz["_id"])
            canonical_quiz_id = legacy_saved_quiz.get("canonical_quiz_id")
            if canonical_quiz_id:
                canonical_quiz = await self.canonical_service.get_quiz_v2_by_id(
                    canonical_quiz_id
                )

        payload = {
            "_id": result_id,
            "user_id": user_id,
            "quiz_id": (
                saved_ref.quiz_id if saved_ref else legacy_saved_quiz.get("quiz_id")
            ),
            "title": (
                (saved_ref.display_title if saved_ref else None)
                or (legacy_saved_quiz.get("title") if legacy_saved_quiz else None)
                or (canonical_quiz.title if canonical_quiz else "Saved Quiz")
            ),
            "question_type": (
                (legacy_saved_quiz.get("question_type") if legacy_saved_quiz else None)
                or (canonical_quiz.quiz_type if canonical_quiz else None)
            ),
            "questions": [],
            "created_at": (
                (self._normalize_datetime(saved_ref.saved_at) if saved_ref else None)
                or (legacy_saved_quiz.get("created_at") if legacy_saved_quiz else None)
            ),
        }
        if legacy_saved_quiz and legacy_saved_quiz.get("questions"):
            payload["questions"] = legacy_saved_quiz["questions"]
        elif canonical_quiz:
            payload["questions"] = [
                {
                    "question": question.question,
                    "options": question.options,
                    "correct_answer": question.correct_answer,
                }
                for question in canonical_quiz.questions
            ]
        if isinstance(payload["created_at"], datetime):
            payload["created_at"] = payload["created_at"].isoformat()
        return payload

    async def delete_saved_quiz(
        self,
        *,
        user_id: str,
        saved_quiz_id: str,
    ) -> bool:
        saved_ref = await self.reference_repository.get_saved_quiz_for_user(
            user_id,
            saved_quiz_id,
        )
        if saved_ref:
            deleted = await self.reference_repository.delete_saved_quiz_for_user(
                user_id,
                saved_quiz_id,
            )
            if not deleted:
                return False
            if saved_ref.legacy_saved_quiz_id:
                try:
                    await self.legacy_saved_quizzes_collection.delete_one(
                        {
                            "_id": ObjectId(saved_ref.legacy_saved_quiz_id),
                            "user_id": user_id,
                        }
                    )
                except InvalidId:
                    pass
            return True

        legacy_saved_quiz = await self._get_legacy_saved_quiz(
            user_id=user_id,
            saved_quiz_id=saved_quiz_id,
        )
        if not legacy_saved_quiz:
            return False

        result = await self.legacy_saved_quizzes_collection.delete_one(
            {"_id": legacy_saved_quiz["_id"], "user_id": user_id}
        )
        if result.deleted_count:
            await self.reference_repository.delete_saved_quiz_by_legacy_id(
                str(legacy_saved_quiz["_id"])
            )
        return result.deleted_count > 0

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
        legacy_saved_quiz = None
        legacy_saved_quiz_id = saved_quiz_id

        if saved_ref:
            legacy_saved_quiz_id = saved_ref.legacy_saved_quiz_id or saved_quiz_id
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
        else:
            legacy_saved_quiz = await self._get_legacy_saved_quiz(
                user_id=user_id,
                saved_quiz_id=saved_quiz_id,
            )
            if not legacy_saved_quiz:
                return None
            legacy_saved_quiz = await self.legacy_saved_quizzes_collection.find_one_and_update(
                {
                    "_id": legacy_saved_quiz["_id"],
                    "user_id": user_id,
                },
                {"$set": {"title": title, "updated_at": datetime.utcnow()}},
                return_document=ReturnDocument.AFTER,
            )
            legacy_saved_quiz_id = str(legacy_saved_quiz["_id"])

        return SavedQuizResponse(
            id=legacy_saved_quiz_id,
            quiz_id=(
                saved_ref.quiz_id
                if saved_ref
                else legacy_saved_quiz.get("quiz_id", "")
            ),
            title=title,
            created_at=(
                self._normalize_datetime(saved_ref.saved_at) if saved_ref else None
            )
            or (legacy_saved_quiz.get("created_at") if legacy_saved_quiz else None),
            question_type=legacy_saved_quiz.get("question_type") if legacy_saved_quiz else None,
        )
