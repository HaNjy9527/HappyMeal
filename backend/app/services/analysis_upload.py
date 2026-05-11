from __future__ import annotations

import logging
import time
from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import AnalysisStatus, User
from app.schemas.analysis import AnalysisCandidateResponse, RecognitionStatus
from app.services.ai_event_log import record_ai_event
from app.services.analysis import get_analysis_for_user
from app.services.analysis_recognition import recognize_analysis_image
from app.services.recognition_openai import RECOGNITION_PROMPT_VERSION


logger = logging.getLogger("app.analysis")


def resolve_analysis_status(recognition_status: RecognitionStatus) -> AnalysisStatus:
    if recognition_status == RecognitionStatus.COMPLETE_FAILURE:
        return AnalysisStatus.DRAFT

    return AnalysisStatus.AWAITING_CONFIRMATION


def validate_image_upload(file: UploadFile) -> None:
    allowed_content_types = {"image/jpeg", "image/png"}

    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG and PNG images are supported",
        )


def build_upload_path(analysis_id: str, filename: str | None) -> Path:
    settings = get_settings()
    suffix = ".jpg"

    if filename:
        filename_suffix = Path(filename).suffix.lower()
        if filename_suffix in {".jpg", ".jpeg", ".png"}:
            suffix = filename_suffix

    settings.analysis_upload_path.mkdir(parents=True, exist_ok=True)
    return settings.analysis_upload_path / f"{analysis_id}{suffix}"


def save_upload_file(file: UploadFile, target_path: Path) -> None:
    settings = get_settings()
    content = file.file.read()

    if len(content) > settings.analysis_max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image exceeds the 5MB upload limit",
        )

    target_path.write_bytes(content)


def delete_analysis_uploads(analysis_id: str) -> None:
    settings = get_settings()

    for file_path in settings.analysis_upload_path.glob(f"{analysis_id}.*"):
        file_path.unlink(missing_ok=True)


def upload_analysis_image(
    db: Session,
    user: User,
    analysis_id: str,
    file: UploadFile,
) -> AnalysisCandidateResponse:
    t0 = time.perf_counter()
    analysis = get_analysis_for_user(db, user, analysis_id)

    if analysis.status != AnalysisStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Image upload is only allowed for draft analyses",
        )

    validate_image_upload(file)
    target_path = build_upload_path(analysis_id, file.filename)

    try:
        save_upload_file(file, target_path)
        recognition_result = recognize_analysis_image(filename=file.filename, image_path=target_path)
    finally:
        delete_analysis_uploads(analysis_id)

    # openai_recognition event（success 或 failure 都寫）
    record_ai_event(
        db,
        event="openai_recognition",
        user_id=user.id,
        analysis_id=analysis_id,
        outcome=recognition_result.provider_outcome,
        reason=recognition_result.provider_reason,
        candidate_count=len(recognition_result.candidates) if recognition_result.provider_outcome == "success" else None,
        input_tokens=recognition_result.provider_input_tokens if recognition_result.provider_outcome == "success" else None,
        output_tokens=recognition_result.provider_output_tokens if recognition_result.provider_outcome == "success" else None,
        latency_ms=recognition_result.provider_latency_ms or None,
        prompt_version=RECOGNITION_PROMPT_VERSION,
    )

    # recognition_result event（僅 API 成功時才有辨識結果可記錄）
    if recognition_result.provider_outcome == "success":
        record_ai_event(
            db,
            event="recognition_result",
            user_id=user.id,
            analysis_id=analysis_id,
            outcome=recognition_result.recognition_status.value,
            candidate_count=len(recognition_result.candidates),
            manual_review_required=recognition_result.manual_review_required,
        )

    analysis.status = resolve_analysis_status(recognition_result.recognition_status)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    latency_ms = round((time.perf_counter() - t0) * 1000)
    logger.info(
        "Analysis upload complete",
        extra={
            "event": "analysis_upload",
            "outcome": "success",
            "latency_ms": latency_ms,
        },
    )

    record_ai_event(
        db,
        event="analysis_upload",
        user_id=user.id,
        analysis_id=analysis_id,
        outcome="success",
        latency_ms=latency_ms,
    )

    return AnalysisCandidateResponse(
        analysis_id=analysis.id,
        status=analysis.status,
        recognition_status=recognition_result.recognition_status,
        candidates=recognition_result.candidates,
        manual_review_required=recognition_result.manual_review_required,
        fallback_reason=recognition_result.fallback_reason,
        message=recognition_result.message,
    )
