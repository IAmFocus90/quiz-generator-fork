from server.app.quiz.utils.huggingface_utils import parse_multichoice


def test_parse_multichoice_strips_separators_and_assistant_chatter():
    response = """1. Which country is the largest by land area in Africa?
A) Nigeria
B) Egypt
C) South Africa
D) Algeria ---
Answer: D) Algeria ---

2. Which African country was never colonized by a European power?
A) Ethiopia
B) Ghana
C) Democratic Republic of the Congo
D) Zimbabwe --- Let me know if you'd like any adjustments!
Answer: A) Ethiopia
"""

    questions = parse_multichoice(response)

    assert questions == [
        {
            "question": "Which country is the largest by land area in Africa?",
            "options": ["A) Nigeria", "B) Egypt", "C) South Africa", "D) Algeria"],
            "answer": "D) Algeria",
            "question_type": "multichoice",
        },
        {
            "question": "Which African country was never colonized by a European power?",
            "options": [
                "A) Ethiopia",
                "B) Ghana",
                "C) Democratic Republic of the Congo",
                "D) Zimbabwe",
            ],
            "answer": "A) Ethiopia",
            "question_type": "multichoice",
        },
    ]
