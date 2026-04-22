from __future__ import annotations

import base64
import json
from decimal import Decimal
from pathlib import Path

from openai import OpenAI

from app.core.config import get_settings
from app.services.recognition_provider import ProviderCandidate


MOCK_CANDIDATE_PRESETS = {
    "salad": [
        ProviderCandidate(
            food_name="Chicken Salad",
            normalized_food_name="chicken_salad",
            confidence_score=Decimal("0.942"),
            portion_default=Decimal("1.00"),
            portion_unit="bowl",
        ),
        ProviderCandidate(
            food_name="Boiled Egg",
            normalized_food_name="boiled_egg",
            confidence_score=Decimal("0.811"),
            portion_default=Decimal("1.00"),
            portion_unit="pcs",
        ),
    ],
    "rice": [
        ProviderCandidate(
            food_name="Grilled Chicken Rice",
            normalized_food_name="grilled_chicken_rice",
            confidence_score=Decimal("0.918"),
            portion_default=Decimal("1.00"),
            portion_unit="plate",
        ),
        ProviderCandidate(
            food_name="Stir-fried Vegetables",
            normalized_food_name="stir_fried_vegetables",
            confidence_score=Decimal("0.768"),
            portion_default=Decimal("0.50"),
            portion_unit="plate",
        ),
    ],
}

DEFAULT_PROVIDER_CANDIDATES = [
    ProviderCandidate(
        food_name="Grilled Salmon",
        normalized_food_name="grilled_salmon",
        confidence_score=Decimal("0.903"),
        portion_default=Decimal("1.00"),
        portion_unit="fillet",
    ),
    ProviderCandidate(
        food_name="Brown Rice",
        normalized_food_name="brown_rice",
        confidence_score=Decimal("0.845"),
        portion_default=Decimal("1.00"),
        portion_unit="bowl",
    ),
    ProviderCandidate(
        food_name="Steamed Broccoli",
        normalized_food_name="steamed_broccoli",
        confidence_score=Decimal("0.732"),
        portion_default=Decimal("0.50"),
        portion_unit="bowl",
    ),
]

OPENAI_RECOGNITION_PROMPT = """
Analyze this single meal photo and identify up to 5 foods or drinks that are clearly visible.

Return JSON only in this shape:
{
  "candidates": [
    {
      "food_name": "display name",
      "normalized_food_name": "snake_case_english_name",
      "confidence_score": 0.0,
      "portion_default": 1.0,
      "portion_unit": "bowl"
    }
  ]
}

Rules:
- Focus on foods and drinks only.
- Prefer Taiwan everyday meal names when appropriate.
- normalized_food_name must be lowercase snake_case English.
- confidence_score must be between 0 and 1.
- portion_default must be a positive number.
- portion_unit must be a short unit like bowl, plate, box, cup, pcs, fillet.
- If uncertain, return fewer items instead of guessing.
- If nothing reliable is visible, return {"candidates": []}.
""".strip()


def create_openai_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.ai_food_api_key)


def get_image_data_url(image_path: Path) -> str:
    suffix = image_path.suffix.lower()
    mime_type = "image/png" if suffix == ".png" else "image/jpeg"
    encoded_image = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded_image}"


def parse_openai_candidate(candidate_payload: dict[str, object]) -> ProviderCandidate | None:
    food_name = str(candidate_payload.get("food_name", "")).strip()
    normalized_food_name = str(candidate_payload.get("normalized_food_name", "")).strip()

    if not food_name or not normalized_food_name:
        return None

    confidence_score = Decimal(str(candidate_payload.get("confidence_score", "0")))
    portion_default = Decimal(str(candidate_payload.get("portion_default", "1")))
    portion_unit = str(candidate_payload.get("portion_unit", "serving")).strip() or "serving"

    clamped_confidence = min(max(confidence_score, Decimal("0")), Decimal("1"))
    safe_portion_default = portion_default if portion_default > 0 else Decimal("1")

    return ProviderCandidate(
        food_name=food_name,
        normalized_food_name=normalized_food_name,
        confidence_score=clamped_confidence,
        portion_default=safe_portion_default,
        portion_unit=portion_unit,
    )


def parse_openai_response(output_text: str) -> list[ProviderCandidate]:
    payload = json.loads(output_text)
    raw_candidates = payload.get("candidates", [])

    if not isinstance(raw_candidates, list):
        return []

    candidates: list[ProviderCandidate] = []

    for raw_candidate in raw_candidates:
        if not isinstance(raw_candidate, dict):
            continue

        candidate = parse_openai_candidate(raw_candidate)
        if candidate is not None:
            candidates.append(candidate)

    return candidates


def request_openai_candidates(*, image_path: Path) -> list[ProviderCandidate]:
    settings = get_settings()
    client = create_openai_client()
    response = client.responses.create(
        model=settings.ai_food_model,
        instructions=OPENAI_RECOGNITION_PROMPT,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Identify the foods and drinks in this meal photo."},
                    {
                        "type": "input_image",
                        "image_url": get_image_data_url(image_path),
                        "detail": "high",
                    },
                ],
            }
        ],
        temperature=0,
        max_output_tokens=400,
    )
    return parse_openai_response(response.output_text)


def recognize_meal_image_with_openai(*, filename: str | None, image_path: Path) -> list[ProviderCandidate]:
    settings = get_settings()

    if settings.ai_food_api_key:
        return request_openai_candidates(image_path=image_path)

    if filename:
        normalized_filename = filename.lower()

        if "salad" in normalized_filename:
            return MOCK_CANDIDATE_PRESETS["salad"]

        if "rice" in normalized_filename:
            return MOCK_CANDIDATE_PRESETS["rice"]

    return DEFAULT_PROVIDER_CANDIDATES