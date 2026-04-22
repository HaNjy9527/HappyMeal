from decimal import Decimal
from pathlib import Path

from app.services.analysis_recognition import recognize_analysis_image
from app.services.recognition_provider import ProviderCandidate
from app.services.recognition_normalization import normalize_provider_candidates


def test_normalize_provider_candidates_skips_blank_names_and_applies_defaults():
    candidates = [
        ProviderCandidate(
            food_name="  Chicken Salad  ",
            normalized_food_name=" chicken_salad ",
            confidence_score=Decimal("0.912"),
            portion_default=Decimal("1.00"),
            portion_unit=" bowl ",
        ),
        ProviderCandidate(
            food_name="",
            normalized_food_name="invalid",
            confidence_score=Decimal("0.500"),
            portion_default=Decimal("1.00"),
            portion_unit="plate",
        ),
        ProviderCandidate(
            food_name="Black Tea",
            normalized_food_name="black_tea",
            confidence_score=Decimal("0.601"),
            portion_default=Decimal("0.00"),
            portion_unit="",
        ),
    ]

    normalized_candidates = normalize_provider_candidates(candidates)

    assert len(normalized_candidates) == 2
    assert normalized_candidates[0].food_name == "Chicken Salad"
    assert normalized_candidates[0].normalized_food_name == "chicken_salad"
    assert normalized_candidates[0].portion_unit == "bowl"
    assert normalized_candidates[1].food_name == "Black Tea"
    assert normalized_candidates[1].portion_default == Decimal("1.00")
    assert normalized_candidates[1].portion_unit == "serving"


def test_recognize_analysis_image_uses_provider_output(monkeypatch):
    provider_candidates = [
        ProviderCandidate(
            food_name="Lunch Box",
            normalized_food_name="lunch_box",
            confidence_score=Decimal("0.873"),
            portion_default=Decimal("1.00"),
            portion_unit="box",
        )
    ]

    def fake_recognize_meal_image_with_openai(*, filename: str | None, image_path: Path):
        assert filename == "meal.jpg"
        assert image_path == Path("tmp/meal.jpg")
        return provider_candidates

    monkeypatch.setattr(
        "app.services.analysis_recognition.recognize_meal_image_with_openai",
        fake_recognize_meal_image_with_openai,
    )

    candidates = recognize_analysis_image(filename="meal.jpg", image_path=Path("tmp/meal.jpg"))

    assert len(candidates) == 1
    assert candidates[0].food_name == "Lunch Box"
    assert candidates[0].normalized_food_name == "lunch_box"