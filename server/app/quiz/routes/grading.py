from typing import List

from fastapi import APIRouter, HTTPException, Query

from server.app.quiz.models.grading_models import UserAnswer
from server.app.quiz.utils.grading import grade_answers


router = APIRouter()


@router.post("/grade-answers")
async def grade_user_answers(
    user_answers: List[UserAnswer],
    source: str = Query("mock", enum=["mock", "ai"]),
):
    try:
        return grade_answers([ua.model_dump() for ua in user_answers], source)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error grading answers: {str(exc)}")
