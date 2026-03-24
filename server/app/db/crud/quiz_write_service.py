from datetime import datetime
from typing import Optional

from server.app.db.core.connection import get_quizzes_v2_collection
from server.app.db.v2.constants import QUIZ_SCHEMA_VERSION
from server.app.db.v2.models.quiz_models import (
    QuizCreateV2,
    QuizDocumentV2,
    QuizMetadataUpdateV2,
    QuizQuestionsUpdateV2,
)
from server.app.db.v2.repositories.quiz_repository import QuizV2Repository


class CanonicalQuizWriteService:
    def __init__(self, repository: Optional[QuizV2Repository] = None):
        self.repository = repository or QuizV2Repository(get_quizzes_v2_collection())

    async def create_quiz_v2(self, quiz_data: QuizCreateV2) -> QuizDocumentV2:
        now = datetime.utcnow()
        quiz_document = QuizDocumentV2(
            title=quiz_data.title.strip(),
            description=quiz_data.description,
            quiz_type=quiz_data.quiz_type,
            owner_user_id=quiz_data.owner_user_id,
            visibility=quiz_data.visibility,
            status=quiz_data.status,
            source=quiz_data.source,
            questions=quiz_data.questions,
            tags=[tag.strip() for tag in quiz_data.tags if tag.strip()],
            schema_version=QUIZ_SCHEMA_VERSION,
            created_at=now,
            updated_at=now,
        )
        return await self.repository.insert_quiz(quiz_document)

    async def update_quiz_metadata_v2(
        self,
        quiz_id: str,
        update_data: QuizMetadataUpdateV2,
    ) -> Optional[QuizDocumentV2]:
        return await self.repository.update_metadata(quiz_id, update_data)

    async def update_quiz_questions_v2(
        self,
        quiz_id: str,
        update_data: QuizQuestionsUpdateV2,
    ) -> Optional[QuizDocumentV2]:
        return await self.repository.update_questions(quiz_id, update_data)

    async def get_quiz_v2_by_id(self, quiz_id: str) -> Optional[QuizDocumentV2]:
        return await self.repository.find_by_id(quiz_id)

    async def soft_delete_quiz_v2(self, quiz_id: str) -> Optional[QuizDocumentV2]:
        return await self.repository.soft_delete(quiz_id)
