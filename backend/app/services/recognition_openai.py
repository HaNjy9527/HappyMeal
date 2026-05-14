from __future__ import annotations

import base64
import io
import json
import logging
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from openai import APIConnectionError, APITimeoutError, BadRequestError, OpenAI, RateLimitError
from PIL import Image

from app.core.config import get_settings
from app.services.recognition_provider import ProviderCandidate


logger = logging.getLogger("app.analysis")

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

RECOGNITION_PROMPT_VERSION = "v2"
REESTIMATE_PROMPT_VERSION = "v2"

OPENAI_RECOGNITION_PROMPT = """
Analyze this single meal photo and identify up to 5 foods or drinks that are clearly visible.

Return JSON only in this shape:
{
  "candidates": [
    {
      "food_name": "正體中文名稱",
      "normalized_food_name": "snake_case_english_name",
      "food_type": "protein",
      "confidence_score": 0.0,
      "portion_default": 1.0,
      "portion_unit": "bowl"
    }
  ]
}

Rules:
- Focus on foods and drinks only.
- food_name must be in Traditional Chinese (正體中文).
- normalized_food_name must be lowercase snake_case English.
- food_type must be one of: condiment, garnish, protein, vegetable, grain, beverage, mixed_meal, dessert, snack.
- confidence_score must be between 0 and 1.
- portion_default must be a positive number.
- portion_unit must be a short unit like bowl, plate, box, cup, pcs, fillet.
- If uncertain, return fewer items instead of guessing.
- If nothing reliable is visible, return {"candidates": []}.
""".strip()

OPENAI_REESTIMATE_PROMPT = """
You are helping revise a meal analysis draft.

You will receive:
- the current meal items the user is editing
- an optional user instruction that corrects names or portions

Return JSON only in this shape:
{
    "candidates": [
        {
            "food_name": "正體中文名稱",
            "normalized_food_name": "snake_case_english_name",
            "food_type": "protein",
            "confidence_score": 0.0,
            "portion_default": 1.0,
            "portion_unit": "bowl"
        }
    ]
}

Rules:
- Treat the user instruction as high-priority correction context.
- If the user says the label is wrong, prefer the corrected label.
- If the user says they ate half, adjust the portion accordingly.
- food_name must be in Traditional Chinese (正體中文).
- normalized_food_name must be lowercase snake_case English.
- food_type must be one of: condiment, garnish, protein, vegetable, grain, beverage, mixed_meal, dessert, snack.
- Keep the candidate list short and practical.
- Do not invent extra foods unless the instruction strongly implies them.
""".strip()


@dataclass(frozen=True)
class ProviderCallResult:
    """Provider API 呼叫結果，含 token 用量與延遲。"""

    candidates: list[ProviderCandidate]
    input_tokens: int
    output_tokens: int
    latency_ms: int
    outcome: str          # "success" | "failure"
    reason: str | None = None


@dataclass(slots=True)
class RecognitionProviderFailure(Exception):
    reason: str
    message: str
    manual_review_required: bool = False
    latency_ms: int = 0   # 供上層寫 event log 用

    def __post_init__(self) -> None:
        super().__init__(self.message)


def create_openai_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.ai_food_api_key)


def preprocess_image(image_path: Path, max_px: int) -> tuple[bytes, str]:
    """長邊超過 max_px 時縮小，統一輸出 JPEG quality=85。"""
    with Image.open(image_path) as img:
        if img.mode != "RGB":
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img)
            img = background

        width, height = img.size
        long_edge = max(width, height)
        if long_edge > max_px:
            scale = max_px / long_edge
            new_size = (int(width * scale), int(height * scale))
            img = img.resize(new_size, Image.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        return buffer.getvalue(), "image/jpeg"


def get_image_data_url(image_path: Path) -> str:
    settings = get_settings()

    if settings.image_preprocess_enabled:
        image_bytes, mime_type = preprocess_image(image_path, settings.image_preprocess_max_px)
    else:
        suffix = image_path.suffix.lower()
        mime_type = "image/png" if suffix == ".png" else "image/jpeg"
        image_bytes = image_path.read_bytes()

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded_image}"


def parse_openai_candidate(candidate_payload: dict[str, object]) -> ProviderCandidate | None:
    food_name = str(candidate_payload.get("food_name", "")).strip()
    normalized_food_name = str(candidate_payload.get("normalized_food_name", "")).strip()

    if not food_name or not normalized_food_name:
        return None

    confidence_score = Decimal(str(candidate_payload.get("confidence_score", "0")))
    portion_default = Decimal(str(candidate_payload.get("portion_default", "1")))
    portion_unit = str(candidate_payload.get("portion_unit", "serving")).strip() or "serving"
    food_type = str(candidate_payload.get("food_type", "")).strip() or None

    clamped_confidence = min(max(confidence_score, Decimal("0")), Decimal("1"))
    safe_portion_default = portion_default if portion_default > 0 else Decimal("1")

    return ProviderCandidate(
        food_name=food_name,
        normalized_food_name=normalized_food_name,
        confidence_score=clamped_confidence,
        portion_default=safe_portion_default,
        portion_unit=portion_unit,
        food_type=food_type,
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


def request_openai_candidates(*, image_path: Path) -> ProviderCallResult:
    settings = get_settings()
    client = create_openai_client()
    t0 = time.perf_counter()
    try:
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
    except RateLimitError as error:
        latency_ms = round((time.perf_counter() - t0) * 1000)
        logger.warning(
            "OpenAI recognition quota exceeded",
            extra={"event": "openai_recognition", "outcome": "failure", "reason": "quota_exceeded", "latency_ms": latency_ms},
        )
        raise RecognitionProviderFailure(
            reason="quota_exceeded",
            message="AI 服務目前額度不足，請重拍、換圖或稍後再試。",
            latency_ms=latency_ms,
        ) from error
    except BadRequestError as error:
        latency_ms = round((time.perf_counter() - t0) * 1000)
        logger.warning(
            "OpenAI recognition invalid image",
            extra={"event": "openai_recognition", "outcome": "failure", "reason": "invalid_image", "latency_ms": latency_ms},
        )
        raise RecognitionProviderFailure(
            reason="invalid_image",
            message="這張圖片目前無法穩定分析，請重拍或改用其他圖片。",
            latency_ms=latency_ms,
        ) from error
    except APITimeoutError as error:
        latency_ms = round((time.perf_counter() - t0) * 1000)
        logger.warning(
            "OpenAI recognition timeout",
            extra={"event": "openai_recognition", "outcome": "failure", "reason": "provider_timeout", "latency_ms": latency_ms},
        )
        raise RecognitionProviderFailure(
            reason="provider_timeout",
            message="AI 分析逾時，請重拍、換圖或稍後再試。",
            latency_ms=latency_ms,
        ) from error
    except APIConnectionError as error:
        latency_ms = round((time.perf_counter() - t0) * 1000)
        logger.warning(
            "OpenAI recognition connection error",
            extra={"event": "openai_recognition", "outcome": "failure", "reason": "provider_unavailable", "latency_ms": latency_ms},
        )
        raise RecognitionProviderFailure(
            reason="provider_unavailable",
            message="AI 服務目前無法連線，請重拍、換圖或稍後再試。",
            latency_ms=latency_ms,
        ) from error

    latency_ms = round((time.perf_counter() - t0) * 1000)
    candidates = parse_openai_response(response.output_text)
    logger.info(
        "OpenAI recognition complete",
        extra={
            "event": "openai_recognition",
            "outcome": "success",
            "candidate_count": len(candidates),
            "latency_ms": latency_ms,
        },
    )
    return ProviderCallResult(
        candidates=candidates,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        latency_ms=latency_ms,
        outcome="success",
    )


def request_openai_reestimate_candidates(
    *,
    items_payload: list[dict[str, object]],
    user_instruction: str | None,
) -> ProviderCallResult:
    settings = get_settings()
    client = create_openai_client()
    instruction_payload = {
        "items": items_payload,
        "user_instruction": user_instruction or "",
    }

    t0 = time.perf_counter()
    try:
        response = client.responses.create(
            model=settings.ai_food_model,
            instructions=OPENAI_REESTIMATE_PROMPT,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(instruction_payload, ensure_ascii=False),
                        }
                    ],
                }
            ],
            temperature=0,
            max_output_tokens=400,
        )
    except RateLimitError as error:
        latency_ms = round((time.perf_counter() - t0) * 1000)
        logger.warning(
            "OpenAI reestimate quota exceeded",
            extra={"event": "openai_reestimate", "outcome": "failure", "reason": "quota_exceeded", "latency_ms": latency_ms},
        )
        raise RecognitionProviderFailure(
            reason="quota_exceeded",
            message="AI 服務目前額度不足，暫時無法重新估算，請稍後再試。",
            latency_ms=latency_ms,
        ) from error
    except BadRequestError as error:
        latency_ms = round((time.perf_counter() - t0) * 1000)
        logger.warning(
            "OpenAI reestimate invalid input",
            extra={"event": "openai_reestimate", "outcome": "failure", "reason": "invalid_image", "latency_ms": latency_ms},
        )
        raise RecognitionProviderFailure(
            reason="invalid_image",
            message="這次的資料無法重新估算，請重新開始分析。",
            latency_ms=latency_ms,
        ) from error
    except APITimeoutError as error:
        latency_ms = round((time.perf_counter() - t0) * 1000)
        logger.warning(
            "OpenAI reestimate timeout",
            extra={"event": "openai_reestimate", "outcome": "failure", "reason": "provider_timeout", "latency_ms": latency_ms},
        )
        raise RecognitionProviderFailure(
            reason="provider_timeout",
            message="AI 重新估算逾時，請稍後再試。",
            latency_ms=latency_ms,
        ) from error
    except APIConnectionError as error:
        latency_ms = round((time.perf_counter() - t0) * 1000)
        logger.warning(
            "OpenAI reestimate connection error",
            extra={"event": "openai_reestimate", "outcome": "failure", "reason": "provider_unavailable", "latency_ms": latency_ms},
        )
        raise RecognitionProviderFailure(
            reason="provider_unavailable",
            message="AI 服務目前無法連線，暫時無法重新估算。",
            latency_ms=latency_ms,
        ) from error

    latency_ms = round((time.perf_counter() - t0) * 1000)
    candidates = parse_openai_response(response.output_text)
    logger.info(
        "OpenAI reestimate complete",
        extra={
            "event": "openai_reestimate",
            "outcome": "success",
            "candidate_count": len(candidates),
            "latency_ms": latency_ms,
        },
    )
    return ProviderCallResult(
        candidates=candidates,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        latency_ms=latency_ms,
        outcome="success",
    )


def recognize_meal_image_with_openai(*, filename: str | None, image_path: Path) -> ProviderCallResult:
    settings = get_settings()

    if settings.ai_food_api_key:
        return request_openai_candidates(image_path=image_path)

    # Mock path（無 API key 時，依 filename 回傳假資料）
    if filename:
        normalized_filename = filename.lower()
        if "salad" in normalized_filename:
            mock_candidates = MOCK_CANDIDATE_PRESETS["salad"]
        elif "rice" in normalized_filename:
            mock_candidates = MOCK_CANDIDATE_PRESETS["rice"]
        else:
            mock_candidates = DEFAULT_PROVIDER_CANDIDATES
    else:
        mock_candidates = DEFAULT_PROVIDER_CANDIDATES

    return ProviderCallResult(
        candidates=mock_candidates,
        input_tokens=0,
        output_tokens=0,
        latency_ms=0,
        outcome="success",
    )


def reestimate_meal_items_with_openai(
    *,
    items_payload: list[dict[str, object]],
    user_instruction: str | None,
) -> ProviderCallResult:
    settings = get_settings()

    if settings.ai_food_api_key:
        return request_openai_reestimate_candidates(
            items_payload=items_payload,
            user_instruction=user_instruction,
        )

    return ProviderCallResult(
        candidates=[],
        input_tokens=0,
        output_tokens=0,
        latency_ms=0,
        outcome="success",
    )