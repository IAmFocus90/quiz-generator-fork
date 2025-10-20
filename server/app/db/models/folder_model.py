from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class FolderModel(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    name: str
    quizzes: List[str] = []  # store quiz_ids from saved_quizzes
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True
        json_encoders = {ObjectId: str}

class FolderCreate(BaseModel):
    user_id: str
    name: str

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    quizzes: Optional[List[str]] = None
