from sqlalchemy.orm import Session

from app.models import AuditEvent


def record_event(
    db: Session,
    *,
    event_type: str,
    description: str,
    user_id: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
) -> None:
    """Persist a security-relevant audit event. Never pass secrets/passwords in `description`."""
    db.add(
        AuditEvent(
            user_id=user_id,
            event_type=event_type,
            description=description,
            target_type=target_type,
            target_id=target_id,
        )
    )
    db.commit()
