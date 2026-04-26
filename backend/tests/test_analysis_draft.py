from decimal import Decimal
from io import BytesIO

import pytest

from app.core.config import get_settings
from app.db.models import ExerciseCatalog
from app.services.analysis_recognition import AnalysisRecognitionResult
from app.services.consent import CURRENT_NON_MEDICAL_DISCLOSURE_VERSION, CURRENT_PRIVACY_POLICY_VERSION


@pytest.fixture
def isolated_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ANALYSIS_UPLOAD_DIR", str(tmp_path))
    get_settings.cache_clear()

    try:
        yield tmp_path
    finally:
        get_settings.cache_clear()


@pytest.fixture(autouse=True)
def disable_real_ai_provider(monkeypatch):
    monkeypatch.setenv("AI_API_KEY", "")
    get_settings.cache_clear()

    try:
        yield
    finally:
        get_settings.cache_clear()


def seed_exercises(db_session):
    db_session.add_all(
        [
            ExerciseCatalog(name="Bodyweight Training", category="strength", met_value=Decimal("3.80"), display_order=1),
            ExerciseCatalog(name="Weight Training", category="strength", met_value=Decimal("6.00"), display_order=2),
            ExerciseCatalog(name="Yoga", category="mind_body", met_value=Decimal("2.50"), display_order=3),
        ]
    )
    db_session.commit()


def build_profile_payload():
    return {
        "age": 28,
        "height_cm": 168,
        "weight_kg": "60.0",
        "activity_level": "moderate",
        "goal_type": "muscle_gain",
        "goal_weight_kg": "62.0",
    }


def accept_required_consents(client):
    privacy_response = client.post(
        "/consents",
        json={
            "consent_type": "privacy_policy",
            "policy_version": CURRENT_PRIVACY_POLICY_VERSION,
        },
    )
    disclosure_response = client.post(
        "/consents",
        json={
            "consent_type": "non_medical_disclosure",
            "policy_version": CURRENT_NON_MEDICAL_DISCLOSURE_VERSION,
        },
    )
    assert privacy_response.status_code == 201
    assert disclosure_response.status_code == 201


def create_completed_analysis(client, image_name: str = "salad-lunch.jpg"):
    accept_required_consents(client)
    profile_response = client.put("/profile", json=build_profile_payload())
    assert profile_response.status_code == 200

    draft_response = client.post("/analyses")
    analysis_id = draft_response.json()["id"]
    upload_response = client.post(
        f"/analyses/{analysis_id}/image",
        files={"file": (image_name, BytesIO(b"fake-jpeg-data"), "image/jpeg")},
    )
    assert upload_response.status_code == 200

    confirm_response = client.post(
        f"/analyses/{analysis_id}/confirm",
        json={
            "items": [
                {
                    "food_name": "Chicken Salad",
                    "normalized_food_name": "chicken_salad",
                    "portion_value": "1.0",
                    "portion_unit": "bowl",
                    "confidence_score": "0.942",
                },
                {
                    "food_name": "Boiled Egg",
                    "normalized_food_name": "boiled_egg",
                    "portion_value": "1.0",
                    "portion_unit": "pcs",
                    "confidence_score": "0.811",
                },
            ]
        },
    )
    assert confirm_response.status_code == 200
    return confirm_response.json()


def test_post_analysis_draft_creates_draft_analysis(client):
    accept_required_consents(client)
    response = client.post("/analyses")

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"]
    assert payload["status"] == "draft"
    assert payload["analyzed_at"]


def test_post_analysis_draft_requires_consents(client):
    response = client.post("/analyses")

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "code": "CONSENT_REQUIRED",
        "message": "You must accept the privacy policy and non-medical disclosure before starting a new analysis.",
    }


def test_post_analysis_image_returns_mock_candidates_and_updates_status(client):
    accept_required_consents(client)
    draft_response = client.post("/analyses")
    analysis_id = draft_response.json()["id"]

    upload_response = client.post(
        f"/analyses/{analysis_id}/image",
        files={"file": ("salad-lunch.jpg", BytesIO(b"fake-jpeg-data"), "image/jpeg")},
    )

    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["analysis_id"] == analysis_id
    assert payload["status"] == "awaiting_confirmation"
    assert payload["manual_review_required"] is False
    assert payload["fallback_reason"] is None
    assert payload["message"] is None
    assert len(payload["candidates"]) == 2
    assert payload["candidates"][0]["food_name"] == "Chicken Salad"


def test_post_analysis_image_returns_manual_review_fallback_for_provider_failures(
    client, isolated_upload_dir, monkeypatch
):
    accept_required_consents(client)
    draft_response = client.post("/analyses")
    analysis_id = draft_response.json()["id"]

    def fake_recognize_analysis_image(*, filename, image_path):
        return AnalysisRecognitionResult(
            candidates=[],
            manual_review_required=True,
            fallback_reason="provider_timeout",
            message="AI 分析逾時，請直接手動調整或稍後再試。",
        )

    monkeypatch.setattr(
        "app.services.analysis_upload.recognize_analysis_image",
        fake_recognize_analysis_image,
    )

    upload_response = client.post(
        f"/analyses/{analysis_id}/image",
        files={"file": ("salad-lunch.jpg", BytesIO(b"fake-jpeg-data"), "image/jpeg")},
    )

    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["analysis_id"] == analysis_id
    assert payload["status"] == "awaiting_confirmation"
    assert payload["candidates"] == []
    assert payload["manual_review_required"] is True
    assert payload["fallback_reason"] == "provider_timeout"
    assert payload["message"] == "AI 分析逾時，請直接手動調整或稍後再試。"
    assert not (isolated_upload_dir / f"{analysis_id}.jpg").exists()


def test_post_analysis_image_rejects_non_image_upload(client):
    accept_required_consents(client)
    draft_response = client.post("/analyses")
    analysis_id = draft_response.json()["id"]

    upload_response = client.post(
        f"/analyses/{analysis_id}/image",
        files={"file": ("notes.txt", BytesIO(b"plain-text"), "text/plain")},
    )

    assert upload_response.status_code == 400
    assert upload_response.json()["detail"] == "Only JPG and PNG images are supported"


def test_post_analysis_image_rejects_non_draft_analysis(client):
    accept_required_consents(client)
    draft_response = client.post("/analyses")
    analysis_id = draft_response.json()["id"]

    first_upload = client.post(
        f"/analyses/{analysis_id}/image",
        files={"file": ("salmon.png", BytesIO(b"fake-png-data"), "image/png")},
    )
    second_upload = client.post(
        f"/analyses/{analysis_id}/image",
        files={"file": ("salmon.png", BytesIO(b"fake-png-data"), "image/png")},
    )

    assert first_upload.status_code == 200
    assert second_upload.status_code == 409
    assert second_upload.json()["detail"] == "Image upload is only allowed for draft analyses"


def test_post_analysis_confirm_persists_totals_snapshot_and_cleans_upload(client, db_session, isolated_upload_dir):
    seed_exercises(db_session)
    accept_required_consents(client)

    profile_response = client.put("/profile", json=build_profile_payload())
    assert profile_response.status_code == 200

    draft_response = client.post("/analyses")
    analysis_id = draft_response.json()["id"]

    upload_response = client.post(
        f"/analyses/{analysis_id}/image",
        files={"file": ("salad-lunch.jpg", BytesIO(b"fake-jpeg-data"), "image/jpeg")},
    )

    assert upload_response.status_code == 200
    assert not (isolated_upload_dir / f"{analysis_id}.jpg").exists()

    confirm_response = client.post(
        f"/analyses/{analysis_id}/confirm",
        json={
            "items": [
                {
                    "food_name": "Chicken Salad",
                    "normalized_food_name": "chicken_salad",
                    "portion_value": "1.0",
                    "portion_unit": "bowl",
                    "confidence_score": "0.942",
                },
                {
                    "food_name": "Boiled Egg",
                    "normalized_food_name": "boiled_egg",
                    "portion_value": "1.0",
                    "portion_unit": "pcs",
                    "confidence_score": "0.811",
                },
            ]
        },
    )

    assert confirm_response.status_code == 200
    payload = confirm_response.json()
    assert payload["analysis_id"] == analysis_id
    assert payload["status"] == "completed"
    assert Decimal(str(payload["total_kcal"])) == Decimal("398.00")
    assert Decimal(str(payload["total_protein_g"])) == Decimal("34.50")
    assert Decimal(str(payload["total_fat_g"])) == Decimal("23.30")
    assert Decimal(str(payload["total_carb_g"])) == Decimal("12.60")
    assert len(payload["items"]) == 2
    assert payload["items"][0]["nutrition_source"] == "preset"
    assert payload["items"][0]["is_estimated"] is False
    assert payload["items"][0]["source_portion_unit"] == "bowl"
    assert payload["items"][0]["canonical_food_name"] == "chicken_salad"
    assert Decimal(str(payload["items"][0]["resolved_weight_g"])) == Decimal("280.00")
    assert payload["items"][0]["weight_estimation_method"] == "exact_unit_match"
    assert Decimal(str(payload["recommendation"]["target_calories_kcal"])) == Decimal("2950.00")
    assert len(payload["recommendation"]["recommended_exercises"]) == 3
    assert payload["recommendation"]["recommended_exercises"][0]["category"] == "strength"
    assert payload["disclaimer"]["title"] == "本服務非醫療用途"
    assert payload["disclaimer"]["policy_version"] == CURRENT_NON_MEDICAL_DISCLOSURE_VERSION
    assert not (isolated_upload_dir / f"{analysis_id}.jpg").exists()


def test_post_analysis_confirm_requires_complete_profile(client, isolated_upload_dir):
    accept_required_consents(client)
    draft_response = client.post("/analyses")
    analysis_id = draft_response.json()["id"]

    upload_response = client.post(
        f"/analyses/{analysis_id}/image",
        files={"file": ("salad-lunch.jpg", BytesIO(b"fake-jpeg-data"), "image/jpeg")},
    )

    assert upload_response.status_code == 200

    confirm_response = client.post(
        f"/analyses/{analysis_id}/confirm",
        json={
            "items": [
                {
                    "food_name": "Chicken Salad",
                    "normalized_food_name": "chicken_salad",
                    "portion_value": "1.0",
                    "portion_unit": "bowl",
                }
            ]
        },
    )

    assert confirm_response.status_code == 409
    assert confirm_response.json()["detail"] == "Profile is incomplete for recommendation generation"


def test_post_analysis_confirm_accepts_unknown_foods_and_units_with_fallback_estimates(client, db_session, isolated_upload_dir):
    seed_exercises(db_session)
    accept_required_consents(client)

    profile_response = client.put("/profile", json=build_profile_payload())
    assert profile_response.status_code == 200

    draft_response = client.post("/analyses")
    analysis_id = draft_response.json()["id"]

    upload_response = client.post(
        f"/analyses/{analysis_id}/image",
        files={"file": ("taiwanese-lunch.jpg", BytesIO(b"fake-jpeg-data"), "image/jpeg")},
    )

    assert upload_response.status_code == 200

    confirm_response = client.post(
        f"/analyses/{analysis_id}/confirm",
        json={
            "items": [
                {
                    "food_name": "雞肉飯",
                    "normalized_food_name": "chicken_rice_bowl",
                    "portion_value": "1.0",
                    "portion_unit": "bowl",
                    "confidence_score": "0.95",
                },
                {
                    "food_name": "高麗菜",
                    "normalized_food_name": "cabbage",
                    "portion_value": "1.0",
                    "portion_unit": "bag",
                    "confidence_score": "0.88",
                },
                {
                    "food_name": "薑絲",
                    "normalized_food_name": "ginger_shreds",
                    "portion_value": "1.0",
                    "portion_unit": "tbsp",
                    "confidence_score": "0.86",
                },
                {
                    "food_name": "辣椒醬",
                    "normalized_food_name": "chili_sauce",
                    "portion_value": "1.0",
                    "portion_unit": "tbsp",
                    "confidence_score": "0.84",
                },
                {
                    "food_name": "白飯",
                    "normalized_food_name": "white_rice",
                    "portion_value": "1.0",
                    "portion_unit": "cup",
                    "confidence_score": "0.82",
                },
            ]
        },
    )

    assert confirm_response.status_code == 200
    payload = confirm_response.json()
    assert payload["status"] == "completed"
    assert len(payload["items"]) == 5
    assert Decimal(str(payload["total_kcal"])) > Decimal("0")
    assert payload["items"][1]["portion_unit"] == "bag"
    assert payload["items"][4]["portion_unit"] == "cup"
    assert payload["items"][0]["nutrition_source"] == "alias_mapping"
    assert payload["items"][0]["is_estimated"] is True
    assert payload["items"][0]["canonical_food_name"] == "generic_mixed_meal"
    assert Decimal(str(payload["items"][0]["resolved_weight_g"])) == Decimal("320.00")
    assert payload["items"][1]["weight_estimation_method"] == "common_unit_conversion"
    assert Decimal(str(payload["items"][0]["kcal"])) > Decimal("0")
    assert Decimal(str(payload["items"][3]["kcal"])) > Decimal("0")


def test_post_analysis_confirm_converts_supported_food_units_instead_of_rejecting(client, db_session, isolated_upload_dir):
    seed_exercises(db_session)
    accept_required_consents(client)

    profile_response = client.put("/profile", json=build_profile_payload())
    assert profile_response.status_code == 200

    draft_response = client.post("/analyses")
    analysis_id = draft_response.json()["id"]

    upload_response = client.post(
        f"/analyses/{analysis_id}/image",
        files={"file": ("chicken-rice.jpg", BytesIO(b"fake-jpeg-data"), "image/jpeg")},
    )

    assert upload_response.status_code == 200

    confirm_response = client.post(
        f"/analyses/{analysis_id}/confirm",
        json={
            "items": [
                {
                    "food_name": "Chicken Rice",
                    "normalized_food_name": "grilled_chicken_rice",
                    "portion_value": "1.0",
                    "portion_unit": "bowl",
                    "confidence_score": "0.91",
                }
            ]
        },
    )

    assert confirm_response.status_code == 200
    payload = confirm_response.json()
    assert payload["items"][0]["portion_unit"] == "bowl"
    assert Decimal(str(payload["items"][0]["kcal"])) == Decimal("468.00")
    assert Decimal(str(payload["items"][0]["resolved_weight_g"])) == Decimal("324.00")
    assert payload["items"][0]["weight_estimation_method"] == "common_unit_conversion"


def test_get_analysis_history_returns_completed_items_only(client, db_session, isolated_upload_dir):
    seed_exercises(db_session)
    completed_analysis = create_completed_analysis(client)

    draft_response = client.post("/analyses")
    assert draft_response.status_code == 201

    history_response = client.get("/analyses")

    assert history_response.status_code == 200
    payload = history_response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["analysis_id"] == completed_analysis["analysis_id"]
    assert payload["items"][0]["food_summary"] == "Chicken Salad, Boiled Egg"
    assert payload["items"][0]["recommendation_summary"] == "Bodyweight Training, Weight Training +1 more"
    assert Decimal(str(payload["items"][0]["total_kcal"])) == Decimal("398.00")


def test_get_analysis_detail_returns_saved_items_and_snapshot_without_image_fields(client, db_session, isolated_upload_dir):
    seed_exercises(db_session)
    completed_analysis = create_completed_analysis(client)

    detail_response = client.get(f"/analyses/{completed_analysis['analysis_id']}")

    assert detail_response.status_code == 200
    payload = detail_response.json()
    assert payload["analysis_id"] == completed_analysis["analysis_id"]
    assert payload["status"] == "completed"
    assert payload["food_summary"] == "Chicken Salad, Boiled Egg"
    assert len(payload["items"]) == 2
    assert payload["items"][0]["food_name"] == "Chicken Salad"
    assert len(payload["recommendation"]["recommended_exercises"]) == 3
    assert payload["disclaimer"]["title"] == "本服務非醫療用途"
    assert payload["disclaimer"]["policy_version"] == CURRENT_NON_MEDICAL_DISCLOSURE_VERSION
    assert "image" not in payload
    assert "image_url" not in payload


def test_get_analysis_detail_rejects_non_completed_analysis(client):
    accept_required_consents(client)
    draft_response = client.post("/analyses")
    analysis_id = draft_response.json()["id"]

    detail_response = client.get(f"/analyses/{analysis_id}")

    assert detail_response.status_code == 409
    assert detail_response.json()["detail"] == "History detail is only available for completed analyses"
