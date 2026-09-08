"""Seeds local/demo data: a demo account and a demo organization with two mocked recon runs
(so the Changes view has something to show). Uses only fabricated, clearly-labeled mock data
against example.com -- an IANA-reserved documentation domain -- never a real arbitrary target,
per PROGRAM_REQUIREMENTS.md 11 ("demo environment uses only mock data or intentionally
controlled sources").

Run with:  python -m app.seed
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal, init_db
from app.models import (
    AccessMode,
    Organization,
    ReconResult,
    ReconRun,
    ResultCategory,
    ResultObservation,
    Role,
    RunStatus,
    User,
)
from app.security import hash_password

DEMO_EMAIL = "demo@ethicalhawk-recon.example"


def _mock_results(run_id: str, variant: int) -> list[ReconResult]:
    base = [
        ReconResult(
            run_id=run_id,
            category=ResultCategory.DOMAINS,
            title="example.com",
            summary="Confirmed primary domain.",
            dedupe_key="primary-domain:example.com",
            source_name="Demo/Mock Data",
            source_url="https://example.com/",
            confidence=1.0,
            rationale="Domain selected during organization confirmation.",
        ),
        ReconResult(
            run_id=run_id,
            category=ResultCategory.WEB_PRESENCE,
            title="Official website: example.com",
            summary="Example Demo Corp is a fictional company used for EthicalHawk Recon's own demo data.",
            dedupe_key="official-site:example.com",
            source_name="Demo/Mock Data",
            source_url="https://example.com/",
            confidence=1.0,
        ),
        ReconResult(
            run_id=run_id,
            category=ResultCategory.DNS_NETWORK,
            title="A records for example.com",
            summary="93.184.216.34",
            dedupe_key="dns:example.com:A",
            source_name="Demo/Mock Data",
            source_url=None,
            confidence=1.0,
        ),
        ReconResult(
            run_id=run_id,
            category=ResultCategory.PEOPLE,
            title="J. Rivera -- Founder",
            summary="Publicly attributed as founder in demo source text. (Fabricated for demo purposes.)",
            dedupe_key="person:J. Rivera:Founder",
            source_name="Demo/Mock Data",
            source_url=None,
            confidence=0.5,
        ),
        ReconResult(
            run_id=run_id,
            category=ResultCategory.DOCUMENTS,
            title="Press/News: example.com/press",
            summary="Publicly accessible press page on the confirmed domain. (Demo data.)",
            dedupe_key="public-page:example.com/press",
            source_name="Demo/Mock Data",
            source_url="https://example.com/press",
            confidence=0.9,
        ),
    ]
    if variant == 2:
        base.append(
            ReconResult(
                run_id=run_id,
                category=ResultCategory.DOMAINS,
                title="status.example.com",
                summary="Observed in demo certificate-transparency-style mock data.",
                dedupe_key="subdomain:status.example.com",
                source_name="Demo/Mock Data",
                source_url=None,
                confidence=0.75,
            )
        )
    return base


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == DEMO_EMAIL).one_or_none()
        if user is None:
            password = os.environ.get("DEMO_PASSWORD") or secrets.token_urlsafe(12)
            user = User(email=DEMO_EMAIL, password_hash=hash_password(password), role=Role.ADMINISTRATOR)
            db.add(user)
            db.commit()
            print(f"Created demo user: {DEMO_EMAIL} / {password}")
        else:
            print(f"Demo user already exists: {DEMO_EMAIL}")

        org = db.query(Organization).filter(Organization.primary_domain == "example.com").one_or_none()
        if org is None:
            org = Organization(
                name="Example Demo Corp",
                primary_domain="example.com",
                description="Fictional demo organization used for EthicalHawk Recon's own screenshots and demos.",
                description_source="Demo/Mock Data",
            )
            db.add(org)
            db.commit()

        existing_runs = db.query(ReconRun).filter(ReconRun.organization_id == org.id).count()
        if existing_runs == 0:
            older = ReconRun(
                organization_id=org.id,
                user_id=user.id,
                mode=AccessMode.AUTHORIZED_PASSIVE,
                status=RunStatus.COMPLETED,
                started_at=datetime.now(timezone.utc) - timedelta(days=7),
                completed_at=datetime.now(timezone.utc) - timedelta(days=7),
            )
            older.created_at = datetime.now(timezone.utc) - timedelta(days=7)
            db.add(older)
            db.commit()
            for r in _mock_results(older.id, variant=1):
                db.add(r)
            db.commit()
            for r in older.results:
                db.add(
                    ResultObservation(
                        organization_id=org.id,
                        category=r.category,
                        dedupe_key=r.dedupe_key,
                        first_observed_at=older.created_at,
                        last_observed_at=older.created_at,
                        last_seen_run_id=older.id,
                    )
                )
            db.commit()

            newer = ReconRun(
                organization_id=org.id,
                user_id=user.id,
                mode=AccessMode.AUTHORIZED_PASSIVE,
                status=RunStatus.COMPLETED,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            db.add(newer)
            db.commit()
            for r in _mock_results(newer.id, variant=2):
                db.add(r)
            db.commit()
            print(f"Seeded demo organization '{org.name}' with 2 mock runs.")
        else:
            print(f"Demo organization '{org.name}' already has runs; skipping.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
