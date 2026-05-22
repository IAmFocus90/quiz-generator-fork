import pytest

from server.app.quiz.services.category_taxonomy_service import (
    classify_deterministically,
    display_name_from_path,
    normalize_quiz_type,
    quiz_type_to_api_label,
    slugify,
)


def test_seed_path_display_and_slug_normalization():
    assert display_name_from_path("Art_&_Literature") == "Art and Literature"
    assert display_name_from_path("TV_Series") == "TV Series"
    assert slugify("Art and Literature") == "art-and-literature"


def test_quiz_type_normalization_supports_seed_labels_and_canonical_values():
    assert normalize_quiz_type("multiple choice") == "multichoice"
    assert normalize_quiz_type("true or false") == "true-false"
    assert normalize_quiz_type("open ended") == "open-ended"
    assert normalize_quiz_type("short answer") == "short-answer"
    assert quiz_type_to_api_label("short-answer") == "short answer"


def test_quiz_type_normalization_rejects_unknown_type():
    with pytest.raises(ValueError):
        normalize_quiz_type("essay")


def test_deterministic_classifier_matches_known_taxonomy():
    classification = classify_deterministically(
        "Generate a software engineering quiz about coding algorithms and programming basics.",
        "multichoice",
    )

    assert classification is not None
    assert classification.category_slug == "technology-and-computing"
    assert classification.subcategory_slug == "programming"
    assert classification.method == "deterministic"
    assert "programming" in classification.tags
