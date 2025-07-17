from fastapi import HTTPException
import random
import os
import json
import httpx
from dotenv import load_dotenv

from server.app.quiz.mock_data.multi_choice import mock_multiple_choice_questions
from server.app.quiz.mock_data.true_false import mock_true_false_questions
from server.app.quiz.mock_data.open_ended import mock_open_ended_questions
from server.app.quiz.mock_data.short_answer import mock_short_answer_questions

from server.api.v1.crud.update_quiz_history import update_quiz_history

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

def get_questions(
    question_type: str,
    num_questions: int,
    user_id: str = "defaultUserId",
    profession: str = "general knowledge",
    audience_type: str = "students",
    custom_instruction: str = "",
    difficulty_level: str = "easy"
):
    question_data = {
        "multichoice": mock_multiple_choice_questions,
        "true-false": mock_true_false_questions,
        "open-ended": mock_open_ended_questions,
        "short-answer": mock_short_answer_questions,
    }

    if question_type not in question_data:
        raise HTTPException(status_code=400, detail=f"Invalid question type: {question_type}")

    # Build format instruction
    if question_type == "multichoice":
        format_instruction = (
            "Return a JSON array of objects with keys: question, type, options (a-d), and correct_answer."
        )
    elif question_type == "true-false":
        format_instruction = (
            "Return a JSON array of objects with keys: question, type (true-false), and correct_answer (True or False)."
        )
    elif question_type == "short-answer":
        format_instruction = (
            "Return a JSON array of objects with keys: question, type (short-answer), and correct_answer."
        )
    elif question_type == "open-ended":
        format_instruction = (
            "Return a JSON array of objects with keys: question, type (open-ended), and correct_answer."
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported question type: {question_type}")

    prompt = (
        f"You are a professional quiz creator.\n\n"
        f"Create a {difficulty_level} {question_type.replace('-', ' ')} quiz with {num_questions} questions.\n"
        f"Topic: {profession}\n"
        f"Audience: {audience_type}\n"
        f"Instructions: {custom_instruction or 'None'}\n"
        f"{format_instruction}\n"
        f"Respond in pure JSON with no additional text or commentary."
    )

    try:
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant for quiz generation."},
                {"role": "user", "content": prompt}
            ]
        }

        response = httpx.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]

        try:
            quiz_data = json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse AI response. Invalid JSON.")

        update_quiz_history(user_id, quiz_data)
        return quiz_data

    except Exception as e:
        print("⚠️ AI call failed — using mock data instead:", e)

        fallback = question_data[question_type]
        if num_questions > len(fallback):
            raise HTTPException(
                status_code=400,
                detail=f"Requested {num_questions}, but only {len(fallback)} available in mock data.",
            )

        fallback_data = random.sample(fallback, num_questions)
        update_quiz_history(user_id, fallback_data)
        return fallback_data
