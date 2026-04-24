from datetime import datetime

import pytest
from bson import ObjectId

from server.app.db.core.config import settings


@pytest.mark.asyncio
async def test_stage4_history_v2_only_reads_legacy_compatible_payload(
    read_cutover_db,
    read_service_factory,
    monkeypatch,
):
    service = read_service_factory()
    monkeypatch.setattr(settings, "QUIZ_V2_HISTORY_READ_MODE", "v2_only")

    quiz_id = ObjectId()
    history_id = ObjectId()
    await read_cutover_db["quizzes_v2"].insert_one(
        {
            "_id": quiz_id,
            "title": "Caching",
            "quiz_type": "multichoice",
            "questions": [
                {
                    "question": "What does Redis store?",
                    "options": ["Rows", "Keys"],
                    "correct_answer": "Keys",
                }
            ],
            "description": "Infra topic",
            "owner_user_id": None,
            "visibility": "private",
            "status": "active",
            "source": "legacy",
            "tags": [],
            "legacy_source_collection": "ai_generated_quizzes",
            "legacy_quiz_id": "legacy-ai-1",
            "content_fingerprint": "history-content",
            "structure_fingerprint": "history-structure",
            "schema_version": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "deleted_at": None,
        }
    )
    await read_cutover_db["quiz_history_v2"].insert_one(
        {
            "user_id": "user-1",
            "quiz_id": str(quiz_id),
            "action": "generated",
            "metadata": {"topic": "Caching", "difficulty_level": "easy"},
            "legacy_history_id": str(history_id),
            "created_at": datetime.utcnow(),
        }
    )

    payload = await service.get_quiz_history_for_user("user-1")

    assert len(payload) == 1
    assert payload[0]["id"] is not None
    assert payload[0]["legacy_id"] == str(history_id)
    assert payload[0]["_id"] == str(history_id)
    assert payload[0]["quiz_id"] == str(quiz_id)
    assert payload[0]["legacy_quiz_id"] == "legacy-ai-1"
    assert payload[0]["question_type"] == "multichoice"
    assert payload[0]["questions"][0]["answer"] == "Keys"
    assert payload[0]["questions"][0]["question_type"] == "multichoice"


@pytest.mark.asyncio
async def test_stage4_saved_compare_mode_returns_legacy_contract(
    read_cutover_db,
    read_service_factory,
    monkeypatch,
):
    service = read_service_factory()
    monkeypatch.setattr(settings, "QUIZ_V2_SAVED_READ_MODE", "compare")

    saved_id = ObjectId()
    quiz_id = ObjectId()
    created_at = datetime.utcnow()
    await read_cutover_db["saved_quizzes"].insert_one(
        {
            "_id": saved_id,
            "user_id": "user-1",
            "quiz_id": "legacy-ai-1",
            "title": "Legacy Saved Quiz",
            "question_type": "multichoice",
            "questions": [{"question": "Legacy question", "options": ["A", "B"], "question_type": "multichoice"}],
            "created_at": created_at,
        }
    )
    await read_cutover_db["quizzes_v2"].insert_one(
        {
            "_id": quiz_id,
            "title": "Legacy Saved Quiz",
            "quiz_type": "multichoice",
            "questions": [
                {
                    "question": "Legacy question",
                    "options": ["A", "B"],
                    "correct_answer": "A",
                }
            ],
            "description": None,
            "owner_user_id": None,
            "visibility": "private",
            "status": "active",
            "source": "legacy",
            "tags": [],
            "legacy_source_collection": "ai_generated_quizzes",
            "legacy_quiz_id": "legacy-ai-1",
            "content_fingerprint": "saved-content",
            "structure_fingerprint": "saved-structure",
            "schema_version": 1,
            "created_at": created_at,
            "updated_at": created_at,
            "deleted_at": None,
        }
    )
    await read_cutover_db["saved_quizzes_v2"].insert_one(
        {
            "user_id": "user-1",
            "quiz_id": str(quiz_id),
            "legacy_saved_quiz_id": str(saved_id),
            "saved_at": created_at,
        }
    )

    payload = await service.get_saved_quizzes_for_user("user-1")

    assert len(payload) == 1
    assert payload[0]["_id"] == str(saved_id)
    assert payload[0]["title"] == "Legacy Saved Quiz"
    assert payload[0]["questions"][0]["question"] == "Legacy question"
    assert "correct_answer" not in payload[0]["questions"][0]


@pytest.mark.asyncio
async def test_stage4_saved_v2_only_preserves_legacy_saved_id_and_restores_answers(
    read_cutover_db,
    read_service_factory,
    monkeypatch,
):
    service = read_service_factory()
    monkeypatch.setattr(settings, "QUIZ_V2_SAVED_READ_MODE", "v2_only")

    saved_id = ObjectId()
    quiz_id = ObjectId()
    created_at = datetime.utcnow()
    await read_cutover_db["quizzes_v2"].insert_one(
        {
            "_id": quiz_id,
            "title": "Russian Federation",
            "quiz_type": "multichoice",
            "questions": [
                {
                    "question": "What is the capital of Russia?",
                    "options": ["A) Kyiv", "B) Moscow"],
                    "correct_answer": "B) Moscow",
                }
            ],
            "description": "Geopolitics",
            "owner_user_id": None,
            "visibility": "private",
            "status": "active",
            "source": "legacy",
            "tags": [],
            "legacy_source_collection": "ai_generated_quizzes",
            "legacy_quiz_id": "legacy-russia",
            "content_fingerprint": "saved-content-v2",
            "structure_fingerprint": "saved-structure-v2",
            "schema_version": 1,
            "created_at": created_at,
            "updated_at": created_at,
            "deleted_at": None,
        }
    )
    await read_cutover_db["saved_quizzes_v2"].insert_one(
        {
            "user_id": "user-2",
            "quiz_id": str(quiz_id),
            "display_title": "Russia",
            "legacy_saved_quiz_id": str(saved_id),
            "saved_at": created_at,
        }
    )

    payload = await service.get_saved_quiz_by_id(str(saved_id), "user-2")

    assert payload is not None
    assert payload["id"] is not None
    assert payload["legacy_id"] == str(saved_id)
    assert payload["_id"] == str(saved_id)
    assert payload["title"] == "Russia"
    assert payload["quiz_id"] == str(quiz_id)
    assert payload["legacy_quiz_id"] == "legacy-russia"
    assert payload["canonical_quiz_id"] == str(quiz_id)
    assert payload["questions"][0]["correct_answer"] == "B) Moscow"


@pytest.mark.asyncio
async def test_stage4_folder_v2_only_preserves_folder_and_item_legacy_ids_and_position(
    read_cutover_db,
    read_service_factory,
    monkeypatch,
):
    service = read_service_factory()
    monkeypatch.setattr(settings, "QUIZ_V2_FOLDER_READ_MODE", "v2_only")

    folder_v2_id = ObjectId()
    quiz_one_id = ObjectId()
    quiz_two_id = ObjectId()
    created_at = datetime.utcnow()
    await read_cutover_db["folders_v2"].insert_one(
        {
            "_id": folder_v2_id,
            "user_id": "user-folder",
            "name": "Research",
            "legacy_folder_id": "legacy-folder-1",
            "created_at": created_at,
            "updated_at": created_at,
        }
    )
    await read_cutover_db["quizzes_v2"].insert_many(
        [
            {
                "_id": quiz_one_id,
                "title": "United States Military",
                "quiz_type": "multichoice",
                "questions": [{"question": "Q2", "options": ["A", "B"], "correct_answer": "A"}],
                "description": None,
                "owner_user_id": None,
                "visibility": "private",
                "status": "active",
                "source": "legacy",
                "tags": [],
                "legacy_source_collection": "ai_generated_quizzes",
                "legacy_quiz_id": "legacy-quiz-2",
                "content_fingerprint": "folder-content-2",
                "structure_fingerprint": "folder-structure-2",
                "schema_version": 1,
                "created_at": created_at,
                "updated_at": created_at,
                "deleted_at": None,
            },
            {
                "_id": quiz_two_id,
                "title": "Russian Federation",
                "quiz_type": "multichoice",
                "questions": [{"question": "Q1", "options": ["A", "B"], "correct_answer": "B"}],
                "description": None,
                "owner_user_id": None,
                "visibility": "private",
                "status": "active",
                "source": "legacy",
                "tags": [],
                "legacy_source_collection": "ai_generated_quizzes",
                "legacy_quiz_id": "legacy-quiz-1",
                "content_fingerprint": "folder-content-1",
                "structure_fingerprint": "folder-structure-1",
                "schema_version": 1,
                "created_at": created_at,
                "updated_at": created_at,
                "deleted_at": None,
            },
        ]
    )
    await read_cutover_db["folder_items_v2"].insert_many(
        [
            {
                "folder_id": str(folder_v2_id),
                "quiz_id": str(quiz_one_id),
                "added_by": "user-folder",
                "position": 1,
                "display_title": "USA Military",
                "legacy_folder_item_id": "item-2",
                "created_at": created_at,
            },
            {
                "folder_id": str(folder_v2_id),
                "quiz_id": str(quiz_two_id),
                "added_by": "user-folder",
                "position": 0,
                "display_title": "Russia",
                "legacy_folder_item_id": "item-1",
                "created_at": created_at,
            },
        ]
    )

    payload = await service.get_folder_by_id("legacy-folder-1", "user-folder")

    assert payload is not None
    assert payload["id"] == str(folder_v2_id)
    assert payload["legacy_id"] == "legacy-folder-1"
    assert payload["_id"] == "legacy-folder-1"
    assert [item["_id"] for item in payload["quizzes"]] == ["item-1", "item-2"]
    assert all(item.get("id") for item in payload["quizzes"])
    assert payload["quizzes"][0]["quiz_id"] == str(quiz_two_id)
    assert payload["quizzes"][0]["legacy_quiz_id"] == "legacy-quiz-1"
    assert payload["quizzes"][0]["title"] == "Russia"
    assert payload["quizzes"][1]["title"] == "USA Military"


@pytest.mark.asyncio
async def test_stage4_shared_v2_only_resolves_saved_quiz_legacy_id(
    read_cutover_db,
    shared_read_service_factory,
    monkeypatch,
):
    service = shared_read_service_factory()
    monkeypatch.setattr(settings, "QUIZ_V2_SHARE_READ_MODE", "v2_only")

    saved_id = ObjectId()
    quiz_id = ObjectId()
    created_at = datetime.utcnow()
    await read_cutover_db["quizzes_v2"].insert_one(
        {
            "_id": quiz_id,
            "title": "Shared Quiz",
            "quiz_type": "multichoice",
            "questions": [{"question": "Q1", "options": ["A", "B"], "correct_answer": "B"}],
            "description": "Shared description",
            "owner_user_id": None,
            "visibility": "private",
            "status": "active",
            "source": "legacy",
            "tags": [],
            "legacy_source_collection": "ai_generated_quizzes",
            "legacy_quiz_id": "legacy-shared-ai",
            "content_fingerprint": "shared-content",
            "structure_fingerprint": "shared-structure",
            "schema_version": 1,
            "created_at": created_at,
            "updated_at": created_at,
            "deleted_at": None,
        }
    )
    await read_cutover_db["saved_quizzes_v2"].insert_one(
        {
            "user_id": "user-1",
            "quiz_id": str(quiz_id),
            "legacy_saved_quiz_id": str(saved_id),
            "saved_at": created_at,
        }
    )

    payload = await service.resolve_shared_quiz(str(saved_id))

    assert payload is not None
    assert payload["id"] == str(quiz_id)
    assert payload["legacy_quiz_id"] == "legacy-shared-ai"
    assert payload["title"] == "Shared Quiz"
    assert payload["questions"][0]["correct_answer"] == "B"
