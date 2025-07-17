import os
import openai
from typing import List
import json

# Set the OpenRouter API Key
openai.api_key = os.getenv("OPENROUTER_API_KEY")  # Make sure it's set in your environment

# Point OpenAI client to OpenRouter
openai.base_url = "https://openrouter.ai/api/v1"

# Grading function using OpenRouter
async def grade_answers_openrouter(user_answers: List[dict]) -> List[dict]:
    results = []

    for answer in user_answers:
        question = answer.get("question", "")
        user_response = answer.get("user_answer", "")
        correct_answer = answer.get("correct_answer", "")
        question_type = answer.get("question_type", "open-ended")

        # Prompt setup
        system_prompt = (
            "You are an expert educator tasked with grading student responses. "
            "Grade as objectively as possible. Return a JSON with fields: "
            "`is_correct` (true/false), `result` ('Correct' or 'Incorrect'), "
            "and `accuracy_percentage` (0-100, optional)."
        )

        user_prompt = f"""
Question Type: {question_type}
Question: {question}
Correct Answer: {correct_answer}
Student's Answer: {user_response}

Grade this answer.
""".strip()

        try:
            completion = await openai.ChatCompletion.acreate(
                model="mistralai/mixtral-8x7b",  # Or any available model on OpenRouter
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
            )

            response_text = completion.choices[0].message.content.strip()
            grading_data = json.loads(response_text)

            results.append({
                "question": question,
                "user_answer": user_response,
                "correct_answer": correct_answer,
                "question_type": question_type,
                "is_correct": grading_data.get("is_correct", False),
                "result": grading_data.get("result", "Incorrect"),
                "accuracy_percentage": grading_data.get("accuracy_percentage", None),
            })

        except Exception as e:
            results.append({
                "question": question,
                "user_answer": user_response,
                "correct_answer": correct_answer,
                "question_type": question_type,
                "is_correct": False,
                "result": "Error",
                "accuracy_percentage": None,
                "error": str(e),
            })

    return results
