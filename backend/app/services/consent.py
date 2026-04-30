from sqlalchemy import desc
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models import ConsentRecord, User
from app.schemas.analysis import DisclaimerResponse
from app.schemas.auth import ConsentStatusResponse, RequiredPolicyVersionsResponse
from app.schemas.consent import ConsentCreateRequest


CURRENT_PRIVACY_POLICY_VERSION = "2026-04-v1"
CURRENT_NON_MEDICAL_DISCLOSURE_VERSION = "2026-04-v1"
CONSENT_REQUIRED_ERROR_CODE = "CONSENT_REQUIRED"


def build_required_policy_versions() -> RequiredPolicyVersionsResponse:
    return RequiredPolicyVersionsResponse(
        privacy_policy=CURRENT_PRIVACY_POLICY_VERSION,
        non_medical_disclosure=CURRENT_NON_MEDICAL_DISCLOSURE_VERSION,
    )


def get_latest_consents_by_type(db: Session, user: User) -> dict[str, ConsentRecord]:
    return {consent.consent_type.value: consent for consent in list_current_consents(db, user)}


def build_consent_status(db: Session, user: User) -> ConsentStatusResponse:
    latest_consents = get_latest_consents_by_type(db, user)
    has_privacy_policy = (
        latest_consents.get("privacy_policy") is not None
        and latest_consents["privacy_policy"].policy_version == CURRENT_PRIVACY_POLICY_VERSION
    )
    has_non_medical_disclosure = (
        latest_consents.get("non_medical_disclosure") is not None
        and latest_consents["non_medical_disclosure"].policy_version == CURRENT_NON_MEDICAL_DISCLOSURE_VERSION
    )
    can_start_analysis = has_privacy_policy and has_non_medical_disclosure
    return ConsentStatusResponse(
        has_privacy_policy=has_privacy_policy,
        has_non_medical_disclosure=has_non_medical_disclosure,
        can_start_analysis=can_start_analysis,
        can_view_guidance=can_start_analysis,
    )


def require_analysis_consents(db: Session, user: User) -> None:
    consent_status = build_consent_status(db, user)
    if consent_status.can_start_analysis:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": CONSENT_REQUIRED_ERROR_CODE,
            "message": "You must accept the privacy policy and non-medical disclosure before starting a new analysis.",
        },
    )


def require_guidance_consents(db: Session, user: User) -> None:
    consent_status = build_consent_status(db, user)
    if consent_status.can_view_guidance:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": CONSENT_REQUIRED_ERROR_CODE,
            "message": "You must accept the privacy policy and non-medical disclosure before viewing guidance.",
        },
    )


def build_non_medical_disclaimer() -> DisclaimerResponse:
    return DisclaimerResponse(
        title="本服務非醫療用途",
        body="此建議僅供日常健康管理參考，不構成醫療診斷、治療或處方。若你有健康疑慮，請諮詢合格醫療專業人士。",
        policy_version=CURRENT_NON_MEDICAL_DISCLOSURE_VERSION,
        consent_type="non_medical_disclosure",
    )


def create_consent(db: Session, user: User, payload: ConsentCreateRequest) -> ConsentRecord:
    consent = (
        db.query(ConsentRecord)
        .filter(
            ConsentRecord.user_id == user.id,
            ConsentRecord.consent_type == payload.consent_type,
            ConsentRecord.policy_version == payload.policy_version,
        )
        .one_or_none()
    )

    if consent is not None:
        return consent

    consent = ConsentRecord(
        user_id=user.id,
        consent_type=payload.consent_type,
        policy_version=payload.policy_version,
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


def list_current_consents(db: Session, user: User) -> list[ConsentRecord]:
    consent_rows = (
        db.query(ConsentRecord)
        .filter(ConsentRecord.user_id == user.id)
        .order_by(ConsentRecord.consent_type, desc(ConsentRecord.accepted_at))
        .all()
    )

    latest_by_type: dict[str, ConsentRecord] = {}
    for consent in consent_rows:
        consent_key = consent.consent_type.value
        if consent_key not in latest_by_type:
            latest_by_type[consent_key] = consent

    return list(latest_by_type.values())