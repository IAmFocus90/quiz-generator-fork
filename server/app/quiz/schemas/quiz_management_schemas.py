from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RenameSavedQuizRequest(BaseModel):
    title: str


class SavedQuizResponse(BaseModel):
    id: str = Field(alias="_id")
    quiz_id: str
    title: str
    created_at: Optional[datetime] = None
    question_type: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class SavedQuizRenameResponse(BaseModel):
    message: str
    quiz: SavedQuizResponse


class QuizHistoryQuestionResponse(BaseModel):
    question: str
    options: list[str] | None = None
    answer: str


class QuizHistoryDetailResponse(BaseModel):
    id: str = Field(alias="_id")
    created_at: Optional[datetime] = None
    quiz_name: Optional[str] = None
    question_type: str
    difficulty_level: Optional[str] = None
    profession: Optional[str] = None
    audience_type: Optional[str] = None
    custom_instruction: Optional[str] = None
    questions: list[QuizHistoryQuestionResponse]

    model_config = ConfigDict(populate_by_name=True)


class DeleteResourceResponse(BaseModel):
    message: str
