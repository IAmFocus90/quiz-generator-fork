from fastapi import APIRouter, HTTPException, Body, Depends

from pydantic import BaseModel

from typing import List

from datetime import datetime

from bson import ObjectId


from ....app.db.crud.folder_crud import (

    create_folder,

    get_user_folders,

    add_quiz_to_folder,

    remove_quiz_from_folder,

    rename_folder,

    delete_folder,

    get_folder_by_id,

    move_quiz_between_folders,

    bulk_delete_folders,

    bulk_remove_quizzes_from_folder,

)

from ....app.db.core.connection import get_saved_quizzes_collection

from ....app.db.models.folder_model import FolderCreate, BulkDeleteFoldersRequest, BulkRemoveRequest
from ....app.db.services.quiz_dual_write_service import QuizDualWriteService
from ....app.db.services.quiz_user_library_read_service import QuizUserLibraryReadService

from ....app.dependancies import get_current_user
from ....app.db.core.config import settings


router = APIRouter(tags=["Folders"])


saved_quizzes_collection = get_saved_quizzes_collection()
read_service = QuizUserLibraryReadService()
write_service = QuizDualWriteService()



class QuizData(BaseModel):

    quiz_id: str



class MoveQuizRequest(BaseModel):

    quiz_id: str

    from_folder_id: str

    to_folder_id: str



class RenameFolderRequest(BaseModel):

    new_name: str





@router.post("/create")

async def create_new_folder(folder: FolderCreate, user = Depends(get_current_user)):

    folder.user_id = user.id
    if settings.QUIZ_V2_WRITE_MODE == "v2_only":
        new_folder = await write_service.create_folder_v2(
            user_id=user.id,
            name=folder.name,
        )
        return {
            "message": "Folder created successfully",
            "folder": {
                "id": str(new_folder.id),
                "_id": str(new_folder.id),
                "user_id": new_folder.user_id,
                "name": new_folder.name,
                "quizzes": [],
                "created_at": new_folder.created_at.isoformat(),
                "updated_at": new_folder.updated_at.isoformat(),
            },
        }

    new_folder = await create_folder(folder.dict())

    return {"message": "Folder created successfully", "folder": new_folder}



@router.get("/")

async def get_folders_for_user(user = Depends(get_current_user)):

    folders = await read_service.get_user_folders(user.id)

    return folders



@router.get("/view/{folder_id}")

async def get_folder_by_id_route(folder_id: str, user = Depends(get_current_user)):
    try:
        folder = await read_service.get_folder_by_id(folder_id, user.id)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Unauthorized access to folder")

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    return folder



@router.put("/{folder_id}/rename")

async def rename_existing_folder(

    folder_id: str,

    payload: RenameFolderRequest,

    user = Depends(get_current_user),

):
    try:
        folder = await read_service.get_folder_by_id(folder_id, user.id)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Unauthorized access to folder")

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    if settings.QUIZ_V2_WRITE_MODE == "v2_only":
        updated = await write_service.rename_folder_v2(
            folder_id=folder_id,
            user_id=user.id,
            new_name=payload.new_name,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Folder not found")
        return {"message": "Folder renamed successfully"}

    await rename_folder(folder_id, payload.new_name)

    return {"message": "Folder renamed successfully"}



@router.delete("/{folder_id}")

async def delete_existing_folder(folder_id: str, user = Depends(get_current_user)):
    try:
        folder = await read_service.get_folder_by_id(folder_id, user.id)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Unauthorized access to folder")

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    if settings.QUIZ_V2_WRITE_MODE == "v2_only":
        deleted = await write_service.delete_folder_v2(folder_id=folder_id, user_id=user.id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Folder not found")
        return {"message": "Folder deleted successfully"}

    await delete_folder(folder_id)

    return {"message": "Folder deleted successfully"}



@router.delete("/bulk_delete")

async def bulk_delete_folders_route(req: BulkDeleteFoldersRequest = Body(...), user = Depends(get_current_user)):

    deleted_count = 0

    for fid in req.folder_ids:

        try:
            folder = await read_service.get_folder_by_id(fid, user.id)
        except PermissionError:
            folder = None

        if folder:
            if settings.QUIZ_V2_WRITE_MODE == "v2_only":
                deleted = await write_service.delete_folder_v2(folder_id=fid, user_id=user.id)
                if deleted:
                    deleted_count += 1
            else:
                await bulk_delete_folders([fid])
                deleted_count += 1

    return {"deleted": deleted_count}





@router.post("/{folder_id}/add_quiz")

async def add_quiz_to_folder_route(folder_id: str, quiz_data: QuizData, user = Depends(get_current_user)):
    try:
        folder = await read_service.get_folder_by_id(folder_id, user.id)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Unauthorized access to folder")

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    if settings.QUIZ_V2_WRITE_MODE == "v2_only":
        try:
            _folder_v2, folder_item = await write_service.add_saved_quiz_to_folder_v2(
                folder_id=folder_id,
                saved_quiz_id=quiz_data.quiz_id,
                user_id=user.id,
            )
        except PermissionError:
            raise HTTPException(status_code=403, detail="Unauthorized access to folder")
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

        return {
            "message": "Quiz added to folder successfully",
            "quiz": {
                "id": str(folder_item.id),
                "_id": str(folder_item.id),
                "title": folder_item.display_title,
                "canonical_quiz_id": folder_item.quiz_id,
            },
        }


    quiz_id = quiz_data.quiz_id

    quiz = await saved_quizzes_collection.find_one({"_id": ObjectId(quiz_id)})

    if not quiz:

        raise HTTPException(status_code=404, detail="Quiz not found in saved quizzes")


    def convert_object_ids(doc):

        if isinstance(doc, dict):

            return {k: convert_object_ids(v) for k, v in doc.items()}

        elif isinstance(doc, list):

            return [convert_object_ids(i) for i in doc]

        elif isinstance(doc, ObjectId):

            return str(doc)

        return doc


    quiz_entry = {

        "_id": str(ObjectId()),

        "original_quiz_id": str(quiz["_id"]),
        "quiz_id": quiz.get("quiz_id"),
        "canonical_quiz_id": quiz.get("canonical_quiz_id"),

        "title": quiz.get("title", "Untitled Quiz"),

        "question_type": quiz.get("question_type", "N/A"),

        "questions": quiz.get("questions", []),

        "created_at": quiz.get("created_at"),

        "added_on": datetime.utcnow(),

        "quiz_data": convert_object_ids(quiz),

    }


    await add_quiz_to_folder(folder_id, quiz_entry)

    return {"message": "Quiz added to folder successfully", "quiz": quiz_entry}



@router.post("/{folder_id}/remove/{quiz_id}")

async def remove_quiz(folder_id: str, quiz_id: str, user = Depends(get_current_user)):
    try:
        folder = await read_service.get_folder_by_id(folder_id, user.id)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Unauthorized access to folder")

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    if settings.QUIZ_V2_WRITE_MODE == "v2_only":
        removed = await write_service.remove_folder_item_v2(
            folder_id=folder_id,
            folder_item_id=quiz_id,
            user_id=user.id,
        )
        if not removed:
            raise HTTPException(status_code=404, detail="Quiz not found in folder")
        return {"message": "Quiz removed from folder"}

    await remove_quiz_from_folder(folder_id, quiz_id)

    return {"message": "Quiz removed from folder"}



@router.patch("/move_quiz")

async def move_quiz_between_folders_route(request: MoveQuizRequest, user = Depends(get_current_user)):
    try:
        source = await read_service.get_folder_by_id(request.from_folder_id, user.id)
        target = await read_service.get_folder_by_id(request.to_folder_id, user.id)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    if not source or not target:
        raise HTTPException(status_code=404, detail="Folder not found")

    if settings.QUIZ_V2_WRITE_MODE == "v2_only":
        moved = await write_service.move_folder_item_v2(
            folder_item_id=request.quiz_id,
            source_folder_id=request.from_folder_id,
            target_folder_id=request.to_folder_id,
            user_id=user.id,
        )
        if not moved:
            raise HTTPException(status_code=404, detail="Quiz not found in source folder")
        return {"message": "Quiz moved successfully", "result": None}

    result = await move_quiz_between_folders(
        request.from_folder_id, request.to_folder_id, request.quiz_id
    )

    return {"message": "Quiz moved successfully", "result": result}



@router.post("/{folder_id}/bulk_remove")

async def bulk_remove_quizzes(folder_id: str, request: BulkRemoveRequest, user = Depends(get_current_user)):
    try:
        folder = await read_service.get_folder_by_id(folder_id, user.id)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    if settings.QUIZ_V2_WRITE_MODE == "v2_only":
        removed = 0
        for quiz_id in request.quiz_ids:
            if await write_service.remove_folder_item_v2(
                folder_id=folder_id,
                folder_item_id=quiz_id,
                user_id=user.id,
            ):
                removed += 1
        return {"message": "Quizzes removed successfully", "removed": removed}

    await bulk_remove_quizzes_from_folder(folder_id, request.quiz_ids)

    return {"message": "Quizzes removed successfully"}
