from fastapi import APIRouter, Depends

from server.app.quiz.models.quiz_models import QuizRequest, QuizResponse
from server.app.quiz.utils.questions import get_questions
from server.app.core.dependencies import get_current_user_optional


router = APIRouter()


@router.post("/get-questions", response_model=QuizResponse)

async def get_quiz(

    request: QuizRequest,

    current_user=Depends(get_current_user_optional),

):

    user_id = str(current_user.id) if current_user else None

    return await get_questions(request, user_id=user_id)
