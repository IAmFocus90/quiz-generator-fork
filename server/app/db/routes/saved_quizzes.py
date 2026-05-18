from fastapi import APIRouter, Depends, HTTPException, status

from ....app.db.crud.saved_quiz_crud import save_quiz
from ....app.db.models.saved_quiz_model import SavedQuizModel
from ....app.db.schemas.quiz_management_schemas import (
    RenameSavedQuizRequest,
    SavedQuizRenameResponse,
)
from ....app.db.schemas.user_schemas import UserResponseSchema
from ....app.db.services.quiz_user_library_service import QuizUserLibraryService
from ....app.dependancies import get_current_user


router = APIRouter(prefix="/saved-quizzes", tags=["Saved Quizzes"])
quiz_user_library_service = QuizUserLibraryService()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_saved_quiz(
    quiz: SavedQuizModel,
    current_user: UserResponseSchema = Depends(get_current_user),
):
    try:
        quiz.user_id = str(current_user.id)
        saved_quiz = await save_quiz(
            user_id=quiz.user_id,
            title=quiz.title,
            question_type=quiz.question_type,
            questions=quiz.questions,
            quiz_id=quiz.quiz_id,
        )
        return {
            "message": "Quiz saved successfully",
            "id": str(saved_quiz.id),
            "quiz_id": saved_quiz.quiz_id,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/", status_code=status.HTTP_200_OK)
async def list_saved_quizzes(
    current_user: UserResponseSchema = Depends(get_current_user),
):
    try:
        return await quiz_user_library_service.list_saved_quizzes(
            user_id=str(current_user.id)
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{quiz_id}", status_code=status.HTTP_200_OK)
async def remove_saved_quiz(
    quiz_id: str,
    current_user: UserResponseSchema = Depends(get_current_user),
):
    try:
        deleted = await quiz_user_library_service.delete_saved_quiz(
            user_id=str(current_user.id),
            saved_quiz_id=quiz_id,
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return {"message": "Quiz deleted successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{quiz_id}", status_code=status.HTTP_200_OK)
async def get_saved_quiz(
    quiz_id: str,
    current_user: UserResponseSchema = Depends(get_current_user),
):
    try:
        quiz = await quiz_user_library_service.get_saved_quiz(
            user_id=str(current_user.id),
            saved_quiz_id=quiz_id,
        )
        if not quiz:
            raise HTTPException(
                status_code=404,
                detail="Quiz not found or unauthorized",
            )
        return quiz
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch(
    "/{quiz_id}/rename",
    status_code=status.HTTP_200_OK,
    response_model=SavedQuizRenameResponse,
)
async def rename_saved_quiz_item(
    quiz_id: str,
    payload: RenameSavedQuizRequest,
    current_user: UserResponseSchema = Depends(get_current_user),
):
    try:
        if not payload.title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")

        updated = await quiz_user_library_service.rename_saved_quiz(
            user_id=str(current_user.id),
            saved_quiz_id=quiz_id,
            title=payload.title.strip(),
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Quiz not found")

        return {"message": "Quiz renamed successfully", "quiz": updated}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
