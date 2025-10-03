from fastapi import APIRouter, HTTPException
from ....app.db.crud import saved_quiz_crud

router = APIRouter()

DUMMY_USER = "dummy-user-1"  # replace later with auth

@router.post("/saved-quizzes/")
async def save_quiz(title: str, quiz_data: dict):
    quiz_id = await saved_quiz_crud.save_quiz(DUMMY_USER, title, quiz_data)
    return {"quiz_id": quiz_id, "message": "Quiz saved successfully"}

@router.get("/saved-quizzes/")
async def get_saved_quizzes():
    return await saved_quiz_crud.get_saved_quizzes(DUMMY_USER)

@router.delete("/saved-quizzes/{quiz_id}")
async def delete_quiz(quiz_id: str):
    success = await saved_quiz_crud.delete_quiz(quiz_id)
    if not success:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return {"message": "Quiz deleted successfully"}
