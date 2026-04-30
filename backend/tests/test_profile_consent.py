from app.services.consent import CURRENT_NON_MEDICAL_DISCLOSURE_VERSION, CURRENT_PRIVACY_POLICY_VERSION


def test_get_profile_creates_default_user_and_profile(client):
    response = client.get("/profile")

    assert response.status_code == 200
    payload = response.json()
    assert payload["display_name"] == "HappyMeal Test User"
    assert payload["theme_preference"] == "female_default"
    assert payload["profile"] == {
        "age": None,
        "height_cm": None,
        "weight_kg": None,
        "activity_level": None,
        "goal_type": None,
        "goal_weight_kg": None,
        "updated_at": payload["profile"]["updated_at"],
    }


def test_put_profile_updates_profile_fields(client):
    response = client.put(
        "/profile",
        json={
            "age": 29,
            "height_cm": 168,
            "weight_kg": 58.5,
            "activity_level": "moderate",
            "goal_type": "fat_loss",
            "goal_weight_kg": 55.0,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["profile"]["age"] == 29
    assert payload["profile"]["height_cm"] == 168
    assert payload["profile"]["weight_kg"] == "58.50"
    assert payload["profile"]["activity_level"] == "moderate"
    assert payload["profile"]["goal_type"] == "fat_loss"
    assert payload["profile"]["goal_weight_kg"] == "55.00"


def test_put_theme_preference_persists_user_preference(client):
    response = client.put("/profile/theme", json={"theme_preference": "male_default"})

    assert response.status_code == 200
    assert response.json()["theme_preference"] == "male_default"


def test_post_and_get_current_consents(client):
    create_response = client.post(
        "/consents",
        json={
            "consent_type": "privacy_policy",
            "policy_version": "2026-03-v1",
        },
    )

    assert create_response.status_code == 201
    created_payload = create_response.json()
    assert created_payload["consent_type"] == "privacy_policy"
    assert created_payload["policy_version"] == "2026-03-v1"

    list_response = client.get("/consents/current")

    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert len(list_payload["items"]) == 1
    assert list_payload["items"][0]["consent_type"] == "privacy_policy"


def test_post_same_consent_version_is_idempotent(client):
    payload = {
        "consent_type": "non_medical_disclosure",
        "policy_version": "2026-03-v1",
    }

    first_response = client.post("/consents", json=payload)
    second_response = client.post("/consents", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["id"] == second_response.json()["id"]


def test_auth_me_reports_required_current_consents_after_acceptance(client):
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

    me_response = client.get("/auth/me")

    assert me_response.status_code == 200
    assert me_response.json()["consent_status"] == {
        "has_privacy_policy": True,
        "has_non_medical_disclosure": True,
        "can_start_analysis": True,
        "can_view_guidance": True,
    }


def test_auth_me_treats_outdated_consent_versions_as_incomplete(client):
    old_policy_version = "2026-03-v1"
    privacy_response = client.post(
        "/consents",
        json={
            "consent_type": "privacy_policy",
            "policy_version": old_policy_version,
        },
    )
    disclosure_response = client.post(
        "/consents",
        json={
            "consent_type": "non_medical_disclosure",
            "policy_version": old_policy_version,
        },
    )
    assert privacy_response.status_code == 201
    assert disclosure_response.status_code == 201

    me_response = client.get("/auth/me")

    assert me_response.status_code == 200
    assert me_response.json()["consent_status"] == {
        "has_privacy_policy": False,
        "has_non_medical_disclosure": False,
        "can_start_analysis": False,
        "can_view_guidance": False,
    }
