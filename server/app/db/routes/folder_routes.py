from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List
from ....app.db.crud.folder_crud import (
    create_folder, get_user_folders, add_quiz_to_folder,
    remove_quiz_from_folder, rename_folder, delete_folder,
    get_folder_by_id, move_quiz_between_folders, bulk_delete_folders, bulk_remove_quizzes_from_folder
)
from ....app.db.models.folder_model import FolderCreate

router = APIRouter(tags=["Folders"])

# ---------- Models ----------
class QuizData(BaseModel):
    quiz: dict

class MoveQuizRequest(BaseModel):
    quiz_id: str
    from_folder_id: str
    to_folder_id: str

class BulkDeleteRequest(BaseModel):
    folder_ids: List[str]

# ---------- Routes ----------

@router.post("/create")
async def create_new_folder(folder: FolderCreate):
    new_folder = await create_folder(folder.dict())
    return {"message": "Folder created successfully", "folder": new_folder}

@router.get("/{user_id}")
async def get_folders_for_user(user_id: str):
    folders = await get_user_folders(user_id)
    return folders

@router.post("/{folder_id}/add_quiz")
async def add_quiz(folder_id: str, quiz: QuizData):
    await add_quiz_to_folder(folder_id, quiz.quiz)
    return {"message": "Quiz added to folder"}

@router.post("/{folder_id}/remove/{quiz_id}")
async def remove_quiz(folder_id: str, quiz_id: str):
    await remove_quiz_from_folder(folder_id, quiz_id)
    return {"message": "Quiz removed from folder"}

@router.put("/{folder_id}/rename")
async def rename_existing_folder(folder_id: str, new_name: str):
    await rename_folder(folder_id, new_name)
    return {"message": "Folder renamed successfully"}

@router.delete("/{folder_id}")
async def delete_existing_folder(folder_id: str):
    await delete_folder(folder_id)
    return {"message": "Folder deleted successfully"}

@router.get("/view/{folder_id}")
async def get_folder_by_id_route(folder_id: str):
    folder = await get_folder_by_id(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder

# ---------- ✅ NEW: Move Quiz Between Folders ----------
@router.patch("/move_quiz")
async def move_quiz(request: MoveQuizRequest):
    result = await move_quiz_between_folders(
    request.from_folder_id,
    request.to_folder_id,
    request.quiz_id
)
    return {"message": "Quiz moved successfully", "result": result}

# ---------- ✅ NEW: Bulk Delete Folders ----------
@router.delete("/bulk_delete")
async def bulk_delete(request: BulkDeleteRequest = Body(...)):
    deleted = await bulk_delete_folders(request.folder_ids)
    return {"message": "Folders deleted successfully", "deleted_count": deleted}

class BulkRemoveRequest(BaseModel):
    quiz_ids: List[str]

@router.post("/{folder_id}/bulk_remove")
async def bulk_remove_quizzes(folder_id: str, request: BulkRemoveRequest):
    await bulk_remove_quizzes_from_folder(folder_id, request.quiz_ids)
    return {"message": "Quizzes removed successfully"}

