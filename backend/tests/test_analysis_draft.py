from decimal import Decimal
from io import BytesIO

import pytest

from app.core.config import get_settings
from app.db.models import ExerciseCatalog


@pytest.fixture
def isolated_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ANALYSIS_UPLOAD_DIR", str(tmp_path))
    get_settings.cache_clear()

    try:
        yield tmp_path
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


def create_completed_analysis(client, image_name: str = "salad-lunch.jpg"):
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
    response = client.post("/analyses")

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"]
    assert payload["status"] == "draft"
    assert payload["analyzed_at"]


def test_post_analysis_image_returns_mock_candidates_and_updates_status(client):
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
    assert len(payload["candidates"]) == 2
    assert payload["candidates"][0]["food_name"] == "Chicken Salad"


def test_post_analysis_image_rejects_non_image_upload(client):
    draft_response = client.post("/analyses")
    analysis_id = draft_response.json()["id"]

    upload_response = client.post(
        f"/analyses/{analysis_id}/image",
        files={"file": ("notes.txt", BytesIO(b"plain-text"), "text/plain")},
    )

    assert upload_response.status_code == 400
    assert upload_response.json()["detail"] == "Only JPG and PNG images are supported"


def test_post_analysis_image_rejects_non_draft_analysis(client):
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

    profile_response = client.put("/profile", json=build_profile_payload())
    assert profile_response.status_code == 200

    draft_response = client.post("/analyses")
    analysis_id = draft_response.json()["id"]

    upload_response = client.post(
        f"/analyses/{analysis_id}/image",
        files={"file": ("salad-lunch.jpg", BytesIO(b"fake-jpeg-data"), "image/jpeg")},
    )

    assert upload_response.status_code == 200
    assert (isolated_upload_dir / f"{analysis_id}.jpg").exists()

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
    assert Decimal(str(payload["recommendation"]["target_calories_kcal"])) == Decimal("2950.00")
    assert len(payload["recommendation"]["recommended_exercises"]) == 3
    assert payload["recommendation"]["recommended_exercises"][0]["category"] == "strength"
    assert not (isolated_upload_dir / f"{analysis_id}.jpg").exists()


def test_post_analysis_confirm_requires_complete_profile(client, isolated_upload_dir):
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
    assert "image" not in payload
    assert "image_url" not in payload


def test_get_analysis_detail_rejects_non_completed_analysis(client):
    draft_response = client.post("/analyses")
    analysis_id = draft_response.json()["id"]

    detail_response = client.get(f"/analyses/{analysis_id}")

    assert detail_response.status_code == 409
    assert detail_response.json()["detail"] == "History detail is only available for completed analyses"
