import logging
import random
from fastapi import HTTPException
from typing import Dict

from server.app.quiz.models.quiz_models import QuizRequest
from server.app.quiz.utils.huggingface_utils import generate_quiz_with_huggingface
from server.app.quiz.utils.mock_quiz_generator import get_mock_questions_by_type
from server.app.db.crud.update_quiz_history import update_quiz_history
from server.app.db.crud.ai_generated_quiz_crud import save_ai_generated_quiz


async def get_questions(request: QuizRequest, user_id: str = "defaultUserId") -> Dict:
    """
    Generate quiz questions using Hugging Face AI.
    Falls back to mock data if AI generation fails.
    Automatically saves AI-generated quizzes to the database.
    """
    try:
        # === 1. Attempt Hugging Face AI generation ===
        ai_payload = request.dict()
        response = generate_quiz_with_huggingface(ai_payload)
        questions = response.get("questions")

        # Validate response
        if isinstance(questions, dict) and "error" in questions:
            raise ValueError("Hugging Face returned an error")

        if not questions or len(questions) < request.num_questions:
            raise ValueError("Not enough questions from Hugging Face")

        final_questions = questions[:request.num_questions]

        # Ensure question_type is added to each question
        for q in final_questions:
            q["question_type"] = request.question_type

        source = "huggingface"

        # === 2. Auto-save quiz to MongoDB ===
        ai_quiz = {
            "profession": request.profession,
            "question_type": request.question_type,
            "difficulty_level": request.difficulty_level,
            "num_questions": request.num_questions,
            "audience_type": request.audience_type,
            "custom_instruction": request.custom_instruction,
            "questions": final_questions  # Pass formatted list
        }

        await save_ai_generated_quiz(ai_quiz)

    except Exception as e:
        # === 3. Fallback to mock quiz generation ===
        logging.warning(f"Hugging Face fallback triggered: {e}")
        question_type = request.question_type
        num_questions = request.num_questions

        mock_data = get_mock_questions_by_type(question_type, num_questions)
        if not mock_data:
            raise HTTPException(
                status_code=400,
                detail=f"No mock data for question type: {question_type}"
            )

        if num_questions > len(mock_data):
            raise HTTPException(
                status_code=400,
                detail=f"Requested {num_questions} questions, but only {len(mock_data)} available in mock data."
            )

        final_questions = random.sample(mock_data, num_questions)

        for q in final_questions:
            q["question_type"] = question_type

        source = "mock"

    # === 4. Update quiz history ===
    update_quiz_history(user_id, final_questions)

    # === 5. Return final result ===
    return {
        "source": source,
        "questions": final_questions
    }
