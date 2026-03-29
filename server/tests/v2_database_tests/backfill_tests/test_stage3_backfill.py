import pytest
from bson import ObjectId

from ....app.db.v2.migration.backfill_engine import (
    backfill_folders,
    backfill_quiz_history,
    backfill_quizzes,
    backfill_saved_quizzes,
    run_backfill,
    run_parity_checks,
)


@pytest.mark.asyncio
async def test_stage3_backfill_reuses_ai_origin_for_saved_history_and_folder(
    backfill_db,
    backfill_context_factory,
):
    ai_id = ObjectId()
    await backfill_db["ai_generated_quizzes"].insert_one(
        {
            "_id": ai_id,
            "profession": "Geography",
            "question_type": "multichoice",
            "difficulty_level": "easy",
            "audience_type": "students",
            "questions": [
                {
                    "question": "Capital of Kenya?",
                    "options": ["Nairobi", "Mombasa"],
                    "answer": "Nairobi",
                    "question_type": "multichoice",
                }
            ],
        }
    )
    saved_id = ObjectId()
    await backfill_db["saved_quizzes"].insert_one(
        {
            "_id": saved_id,
            "user_id": "user-1",
            "quiz_id": str(ai_id),
            "title": "Geography",
            "question_type": "multichoice",
            "questions": [
                {"question": "Capital of Kenya?", "options": ["Nairobi", "Mombasa"], "question_type": "multichoice"}
            ],
        }
    )
    history_id = ObjectId()
    await backfill_db["quiz_history"].insert_one(
        {
            "_id": history_id,
            "user_id": "user-1",
            "quiz_id": str(ai_id),
            "profession": "Geography",
            "question_type": "multichoice",
            "difficulty_level": "easy",
            "audience_type": "students",
            "questions": [
                {
                    "question": "Capital of Kenya?",
                    "options": ["Nairobi", "Mombasa"],
                    "answer": "Nairobi",
                    "question_type": "multichoice",
                }
            ],
        }
    )
    folder_id = ObjectId()
    await backfill_db["folders"].insert_one(
        {
            "_id": folder_id,
            "user_id": "user-1",
            "name": "Trips",
            "quizzes": [
                {
                    "_id": "folder-item-1",
                    "original_quiz_id": str(saved_id),
                    "quiz_id": str(ai_id),
                    "questions": [
                        {"question": "Capital of Kenya?", "options": ["Nairobi", "Mombasa"], "question_type": "multichoice"}
                    ],
                    "question_type": "multichoice",
                    "title": "Geography",
                }
            ],
        }
    )
    context = backfill_context_factory()
    await backfill_quizzes(context)
    await backfill_saved_quizzes(context)
    await backfill_quiz_history(context)
    await backfill_folders(context)

    canonical = await backfill_db["quizzes_v2"].find_one(
        {"legacy_source_collection": "ai_generated_quizzes", "legacy_quiz_id": str(ai_id)}
    )
    saved_v2 = await backfill_db["saved_quizzes_v2"].find_one({"user_id": "user-1"})
    history_v2 = await backfill_db["quiz_history_v2"].find_one({"legacy_history_id": str(history_id)})
    folder_item_v2 = await backfill_db["folder_items_v2"].find_one({"legacy_folder_item_id": "folder-item-1"})

    assert canonical is not None
    assert saved_v2["quiz_id"] == str(canonical["_id"])
    assert history_v2["quiz_id"] == str(canonical["_id"])
    assert history_v2["metadata"]["source"] == "ai"
    assert history_v2["metadata"]["topic"] == "Geography"
    assert folder_item_v2["quiz_id"] == str(canonical["_id"])


@pytest.mark.asyncio
async def test_stage3_backfill_is_idempotent(backfill_db, backfill_context_factory):
    ai_id = ObjectId()
    await backfill_db["ai_generated_quizzes"].insert_one(
        {
            "_id": ai_id,
            "profession": "Networks",
            "question_type": "multichoice",
            "questions": [
                {
                    "question": "What is DNS?",
                    "options": ["Name system", "Firewall"],
                    "answer": "Name system",
                    "question_type": "multichoice",
                }
            ],
        }
    )
    context = backfill_context_factory(collections=["quizzes"], run_id="idem-1")
    await backfill_quizzes(context)
    await backfill_quizzes(context)
    assert await backfill_db["quizzes_v2"].count_documents({}) == 1


@pytest.mark.asyncio
async def test_stage3_history_rerun_counts_noop_records_as_skipped(backfill_db, backfill_context_factory):
    ai_id = ObjectId()
    history_id = ObjectId()
    await backfill_db["ai_generated_quizzes"].insert_one(
        {
            "_id": ai_id,
            "profession": "Systems Design",
            "question_type": "multichoice",
            "questions": [
                {
                    "question": "What is caching?",
                    "options": ["Storage", "Queue"],
                    "answer": "Storage",
                    "question_type": "multichoice",
                }
            ],
        }
    )
    await backfill_db["quiz_history"].insert_one(
        {
            "_id": history_id,
            "user_id": "user-1",
            "quiz_id": str(ai_id),
            "profession": "Systems Design",
            "question_type": "multichoice",
            "difficulty_level": "easy",
            "audience_type": "students",
            "questions": [
                {
                    "question": "What is caching?",
                    "options": ["Storage", "Queue"],
                    "answer": "Storage",
                    "question_type": "multichoice",
                }
            ],
        }
    )

    context = backfill_context_factory(collections=["quizzes", "history"], run_id="history-rerun")
    await backfill_quizzes(context)
    first_summary = await backfill_quiz_history(context)
    second_summary = await backfill_quiz_history(context)

    assert first_summary.inserted == 1
    assert second_summary.inserted == 0
    assert second_summary.updated == 0
    assert second_summary.skipped == 1


@pytest.mark.asyncio
async def test_stage3_backfill_dry_run_does_not_write(backfill_db, backfill_context_factory):
    await backfill_db["ai_generated_quizzes"].insert_one(
        {
            "_id": ObjectId(),
            "profession": "History",
            "question_type": "multichoice",
            "questions": [
                {
                    "question": "Who built the pyramids?",
                    "options": ["Egyptians", "Romans"],
                    "answer": "Egyptians",
                    "question_type": "multichoice",
                }
            ],
        }
    )
    context = backfill_context_factory(dry_run=True, collections=["quizzes"], run_id="dry-run")
    summary = await backfill_quizzes(context)
    assert summary.inserted == 1
    assert await backfill_db["quizzes_v2"].count_documents({}) == 0


@pytest.mark.asyncio
async def test_stage3_parity_reports_orphaned_references(backfill_db, backfill_context_factory):
    await backfill_db["saved_quizzes_v2"].insert_one(
        {"user_id": "user-1", "quiz_id": "missing-quiz", "saved_at": __import__("datetime").datetime.utcnow()}
    )
    context = backfill_context_factory(run_id="parity-1")
    report = await run_parity_checks(context)
    assert report.sections["saved"]["orphaned_quiz_refs"] == 1


@pytest.mark.asyncio
async def test_stage3_run_backfill_returns_collection_reports(backfill_db, backfill_context_factory):
    ai_id = ObjectId()
    await backfill_db["ai_generated_quizzes"].insert_one(
        {
            "_id": ai_id,
            "profession": "Biology",
            "question_type": "multichoice",
            "questions": [
                {
                    "question": "What is DNA?",
                    "options": ["Acid", "Cell"],
                    "answer": "Acid",
                    "question_type": "multichoice",
                }
            ],
        }
    )
    context = backfill_context_factory(collections=["quizzes"], run_id="full-run")
    report = await run_backfill(context)
    assert "quizzes" in report.collections
    assert report.collections["quizzes"].inserted == 1


@pytest.mark.asyncio
async def test_stage3_folder_backfill_with_structure_only_payload_does_not_crash(
    backfill_db,
    backfill_context_factory,
):
    ai_id = ObjectId()
    saved_id = ObjectId()
    folder_id = ObjectId()

    await backfill_db["ai_generated_quizzes"].insert_one(
        {
            "_id": ai_id,
            "profession": "Geography",
            "question_type": "multichoice",
            "questions": [
                {
                    "question": "Capital of Kenya?",
                    "options": ["Nairobi", "Mombasa"],
                    "answer": "Nairobi",
                    "question_type": "multichoice",
                }
            ],
        }
    )
    await backfill_db["saved_quizzes"].insert_one(
        {
            "_id": saved_id,
            "user_id": "user-1",
            "title": "Geography",
            "question_type": "multichoice",
            "questions": [
                {"question": "Capital of Kenya?", "options": ["Nairobi", "Mombasa"], "question_type": "multichoice"}
            ],
        }
    )
    await backfill_db["folders"].insert_one(
        {
            "_id": folder_id,
            "user_id": "user-1",
            "name": "Trips",
            "quizzes": [
                {
                    "_id": "folder-item-1",
                    "original_quiz_id": str(saved_id),
                    "questions": [
                        {
                            "question": "Capital of Kenya?",
                            "options": ["Nairobi", "Mombasa"],
                            "question_type": "multichoice",
                        }
                    ],
                    "question_type": "multichoice",
                    "title": "Geography",
                }
            ],
        }
    )

    context = backfill_context_factory(collections=["quizzes", "folders"], run_id="folder-structure-only")
    await backfill_quizzes(context)
    summary = await backfill_folders(context)

    assert summary.malformed == 0
    assert summary.unresolved == 0
    assert summary.inserted == 2


@pytest.mark.asyncio
async def test_stage3_backfill_saved_quiz_without_answers_matches_legacy_ai_source(
    backfill_db,
    backfill_context_factory,
):
    ai_id = ObjectId()
    saved_id = ObjectId()

    await backfill_db["ai_generated_quizzes"].insert_one(
        {
            "_id": ai_id,
            "profession": "Entropy",
            "question_type": "multichoice",
            "questions": [
                {
                    "question": "What is entropy a measure of in a system?",
                    "options": ["Energy", "Disorder", "Temperature", "Volume"],
                    "answer": "Disorder",
                    "question_type": "multichoice",
                }
            ],
        }
    )
    await backfill_db["saved_quizzes"].insert_one(
        {
            "_id": saved_id,
            "user_id": "user-entropy",
            "title": "Entropy Quiz",
            "question_type": "multichoice",
            "questions": [
                {
                    "question": "What is entropy a measure of in a system?",
                    "options": ["Energy", "Disorder", "Temperature", "Volume"],
                    "question_type": "multichoice",
                }
            ],
        }
    )

    context = backfill_context_factory(collections=["saved"], run_id="saved-legacy-structure")
    summary = await backfill_saved_quizzes(context)

    assert summary.unresolved == 0
    assert summary.conflicts == 0
    assert summary.inserted == 1

    saved_v2 = await backfill_db["saved_quizzes_v2"].find_one({"legacy_saved_quiz_id": str(saved_id)})
    canonical = await backfill_db["quizzes_v2"].find_one(
        {"legacy_source_collection": "ai_generated_quizzes", "legacy_quiz_id": str(ai_id)}
    )

    assert saved_v2 is not None
    assert canonical is not None
    assert saved_v2["quiz_id"] == str(canonical["_id"])


@pytest.mark.asyncio
async def test_stage3_backfill_saved_quiz_reports_conflict_for_multiple_legacy_matches(
    backfill_db,
    backfill_context_factory,
):
    await backfill_db["ai_generated_quizzes"].insert_many(
        [
            {
                "_id": ObjectId(),
                "profession": "Entropy",
                "question_type": "multichoice",
                "questions": [
                    {
                        "question": "What is entropy?",
                        "options": ["Order", "Disorder"],
                        "answer": "Disorder",
                        "question_type": "multichoice",
                    }
                ],
            },
            {
                "_id": ObjectId(),
                "profession": "Entropy",
                "question_type": "multichoice",
                "questions": [
                    {
                        "question": "What is entropy?",
                        "options": ["Order", "Disorder"],
                        "answer": "Disorder",
                        "question_type": "multichoice",
                    }
                ],
            },
        ]
    )
    saved_id = ObjectId()
    await backfill_db["saved_quizzes"].insert_one(
        {
            "_id": saved_id,
            "user_id": "user-entropy",
            "title": "Entropy Quiz",
            "question_type": "multichoice",
            "questions": [
                {
                    "question": "What is entropy?",
                    "options": ["Order", "Disorder"],
                    "question_type": "multichoice",
                }
            ],
        }
    )

    context = backfill_context_factory(collections=["saved"], run_id="saved-conflict")
    summary = await backfill_saved_quizzes(context)

    assert summary.inserted == 0
    assert summary.conflicts == 1
    assert summary.unresolved == 0
    assert summary.conflict_examples[0]["record_id"] == str(saved_id)
    assert len(summary.conflict_examples[0]["candidate_ids"]) == 2
    assert await backfill_db["saved_quizzes_v2"].count_documents({}) == 0
