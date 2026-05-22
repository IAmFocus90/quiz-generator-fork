from typing import List, Literal, Optional

from pydantic import BaseModel


class CategoryQuestionResponse(BaseModel):
    question: str
    options: Optional[List[str]] = None
    answer: str
    question_type: Literal["multiple choice", "true or false", "open ended", "short answer"]
    subcategory: Optional[str] = None
