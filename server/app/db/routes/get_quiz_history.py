from fastapi import APIRouter, Depends
from ....app.db.services.quiz_user_library_read_service import QuizUserLibraryReadService
from ....app.dependancies import get_current_user, get_verified_user
from ....app.db.crud.update_quiz_history import get_quiz_history


router = APIRouter()
read_service = QuizUserLibraryReadService()


@router.get("/quiz-history")

async def get_user_quiz_history(current_user=Depends(get_verified_user)):

    """
    Returns quiz history for the currently authenticated user.
    JWT token required in Authorization header.
    """

    user_id = str(current_user.id)

    quizzes = await read_service.get_quiz_history_for_user(user_id)

    return quizzes
