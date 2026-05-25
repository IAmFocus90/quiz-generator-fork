import pytest

from ...app.quiz.repositories.v2.repositories.quiz_repository import QuizV2Repository
from ...app.quiz.services.canonical_quiz_service import CanonicalQuizWriteService
from ...app.quiz.services.category_service import CategoryService
from ...app.quiz.services.category_seed_service import CategorySeedService
from ...app.quiz.services.category_taxonomy_service import get_taxonomy_entry


@pytest.mark.asyncio
async def test_category_seed_service_upserts_categorized_v2_quiz(test_db):
    service = CategorySeedService(
        CanonicalQuizWriteService(QuizV2Repository(test_db["quizzes_v2"]))
    )
    entry = get_taxonomy_entry("Science", "Biology")
    assert entry is not None

    _, first_status = await service.seed_group(
        entry,
        "short-answer",
        [
            {
                "question": "What is the basic unit of life?",
                "answer": "Cell",
                "question_type": "short-answer",
            }
        ],
    )
    _, second_status = await service.seed_group(
        entry,
        "short-answer",
        [
            {
                "question": "What is the basic unit of life?",
                "answer": "Cell",
                "question_type": "short-answer",
            }
        ],
    )

    docs = await test_db["quizzes_v2"].find({}).to_list(length=10)

    assert first_status == "created"
    assert second_status == "unchanged"
    assert len(docs) == 1
    assert docs[0]["title"] == "Biology: Short Answer Quiz"
    assert docs[0]["source"] == "seed"
    assert docs[0]["visibility"] == "public"
    assert docs[0]["category_slug"] == "science"
    assert docs[0]["subcategory_slug"] == "biology"
    assert docs[0]["classification"] == {"method": "seed_path", "confidence": 1.0}

    category_service = CategoryService(QuizV2Repository(test_db["quizzes_v2"]))

    assert await category_service.list_categories() == ["Science"]
    assert await category_service.list_subcategories("Science") == ["Biology"]
    assert await category_service.list_quiz_types("Science", "Biology") == ["short answer"]
    questions = await category_service.list_questions(
        category="Science",
        subcategory="Biology",
        question_type="short answer",
        page=1,
        page_size=10,
    )
    assert questions == [
        {
            "question": "What is the basic unit of life?",
            "answer": "Cell",
            "subcategory": "Biology",
            "question_type": "short answer",
        }
    ]
