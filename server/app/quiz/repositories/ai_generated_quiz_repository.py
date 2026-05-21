import logging

from server.app.quiz.services.canonical_quiz_service import CanonicalQuizWriteService


logger = logging.getLogger(__name__)
canonical_service = CanonicalQuizWriteService()


async def save_ai_generated_quiz(quiz_data: dict):
    try:
        quiz_document = canonical_service.build_quiz_document(
            title=quiz_data.get("profession") or "General Knowledge",
            description=quiz_data.get("custom_instruction"),
            quiz_type=quiz_data.get("question_type", "multichoice"),
            owner_user_id=quiz_data.get("user_id"),
            source="ai",
            questions=quiz_data["questions"],
        )
        canonical_quiz = await canonical_service.find_or_create_quiz_v2_by_fingerprint(quiz_document)
        return {
            "message": "Quiz saved successfully",
            "quiz_id": str(canonical_quiz.id),
            "duplicate": False,
        }
    except Exception as exc:
        logger.error("Error saving quiz: %s", exc)
        raise
