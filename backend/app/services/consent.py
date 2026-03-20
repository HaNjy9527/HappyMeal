from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.models import ConsentRecord, User
from app.schemas.consent import ConsentCreateRequest


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