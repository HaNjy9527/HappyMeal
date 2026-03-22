from io import BytesIO


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
