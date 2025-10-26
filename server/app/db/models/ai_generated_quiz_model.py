from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class AIQuestion(BaseModel):
    """
    Represents a single AI-generated quiz question.
    """
    question: str
    options: Optional[List[str]] = None  # For multiple choice or true/false
    answer: str                  # The correct answer to the question
    question_type: str                   # e.g., "multiple choice", "true or false", "open ended"


class AIGeneratedQuiz(BaseModel):
    """
    Represents an entire AI-generated quiz that will be auto-saved to the database.
    """
    # Unique quiz ID
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Core quiz metadata
    profession: str = Field(default="General Knowledge")
    question_type: str = Field(default="multichoice")  # lowercase to match frontend query
    difficulty_level: str = Field(default="medium")
    num_questions: int = Field(default=5)
    audience_type: str = Field(default="general")
    custom_instruction: Optional[str] = None

    # The generated questions
    questions: List[AIQuestion]

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "id": "b32b98df-676b-4a12-923f-7f56e7bc4721",
                "profession": "Software Engineering",
                "question_type": "multichoice",
                "difficulty_level": "hard",
                "num_questions": 5,
                "audience_type": "students",
                "custom_instruction": "Focus on algorithms and data structures",
                "created_at": "2025-09-05T18:32:00Z",
                "questions": [
                    {
                        "question": "Which algorithm is used to find the shortest path in a weighted graph?",
                        "options": ["DFS", "BFS", "Dijkstra", "Greedy"],
                        "correct_answer": "Dijkstra",
                        "question_type": "multiple choice"
                    },
                    {
                        "question": "The Earth revolves around the Sun.",
                        "options": ["True", "False"],
                        "correct_answer": "True",
                        "question_type": "true or false"
                    }
                ]
            }
        }
