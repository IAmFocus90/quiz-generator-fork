from fastapi import APIRouter, Depends, HTTPException

from ....app.dependancies import get_current_user
from ....app.db.crud.update_quiz_history import get_quiz_history
from ....app.db.schemas.quiz_management_schemas import (
    DeleteResourceResponse,
    QuizHistoryDetailResponse,
)
from ....app.db.services.quiz_user_library_service import QuizUserLibraryService


router = APIRouter()
quiz_user_library_service = QuizUserLibraryService()


@router.get("/quiz-history")
async def get_user_quiz_history(current_user=Depends(get_current_user)):

    """
    Returns quiz history for the currently authenticated user.
    JWT token required in Authorization header.
    """

    user_id = current_user.id

    quizzes = await get_quiz_history(user_id)

    return quizzes


@router.get("/quiz-history/{history_id}", response_model=QuizHistoryDetailResponse)
async def get_quiz_history_details(
    history_id: str,
    current_user=Depends(get_current_user),
):
    quiz = await quiz_user_library_service.get_quiz_history_detail(
        user_id=str(current_user.id),
        history_id=history_id,
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz history item not found")
    return quiz


@router.delete("/quiz-history/{history_id}", response_model=DeleteResourceResponse)
async def delete_quiz_history_entry(
    history_id: str,
    current_user=Depends(get_current_user),
):
    deleted = await quiz_user_library_service.delete_quiz_history_entry(
        user_id=str(current_user.id),
        history_id=history_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Quiz history item not found")
    return {"message": "Quiz history item deleted successfully"}
