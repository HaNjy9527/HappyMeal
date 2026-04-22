import json
from decimal import Decimal
from pathlib import Path

from app.core.config import get_settings
from app.services.analysis_recognition import recognize_analysis_image
from app.services.recognition_openai import parse_openai_response, recognize_meal_image_with_openai
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


def test_parse_openai_response_builds_provider_candidates():
    output_text = json.dumps(
        {
            "candidates": [
                {
                    "food_name": "雞腿便當",
                    "normalized_food_name": "braised_chicken_lunch_box",
                    "confidence_score": 0.84,
                    "portion_default": 1,
                    "portion_unit": "box",
                },
                {
                    "food_name": "",
                    "normalized_food_name": "invalid",
                    "confidence_score": 0.5,
                    "portion_default": 1,
                    "portion_unit": "bowl",
                },
            ]
        }
    )

    candidates = parse_openai_response(output_text)

    assert len(candidates) == 1
    assert candidates[0].food_name == "雞腿便當"
    assert candidates[0].normalized_food_name == "braised_chicken_lunch_box"
    assert candidates[0].confidence_score == Decimal("0.84")


def test_recognize_meal_image_with_openai_uses_real_client_when_key_exists(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_FOOD_MODEL", "gpt-5.4-mini")
    get_settings.cache_clear()

    response_payload = {
        "candidates": [
            {
                "food_name": "Black Tea",
                "normalized_food_name": "black_tea",
                "confidence_score": 0.62,
                "portion_default": 1,
                "portion_unit": "cup",
            }
        ]
    }

    captured_request: dict[str, object] = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured_request.update(kwargs)
            return type("FakeResponse", (), {"output_text": json.dumps(response_payload)})()

    class FakeClient:
        def __init__(self):
            self.responses = FakeResponses()

    monkeypatch.setattr("app.services.recognition_openai.create_openai_client", lambda: FakeClient())

    image_path = tmp_path / "meal.jpg"
    image_path.write_bytes(b"fake-image-bytes")

    try:
        candidates = recognize_meal_image_with_openai(filename="meal.jpg", image_path=image_path)
    finally:
        get_settings.cache_clear()

    assert captured_request["model"] == "gpt-5.4-mini"
    assert candidates[0].food_name == "Black Tea"
    assert candidates[0].portion_unit == "cup"


def test_recognize_meal_image_with_openai_keeps_mock_fallback_without_key(monkeypatch, tmp_path):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    get_settings.cache_clear()

    image_path = tmp_path / "salad-lunch.jpg"
    image_path.write_bytes(b"fake-image-bytes")

    try:
        candidates = recognize_meal_image_with_openai(filename="salad-lunch.jpg", image_path=image_path)
    finally:
        get_settings.cache_clear()

    assert len(candidates) == 2
    assert candidates[0].food_name == "Chicken Salad"