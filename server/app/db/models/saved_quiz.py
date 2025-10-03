from pydantic import BaseModel, Field
from typing import Dict
from datetime import datetime
from bson import ObjectId

class SavedQuiz(BaseModel):
    id: str = Field(default_factory=str, alias="_id")
    user_id: str   # dummy for now
    title: str
    quiz_data: Dict   # full quiz JSON (category, questions, etc.)
    created_at: datetime = datetime.utcnow()
