from app.models import AccessMode, Organization, ReconResult, ReconRun, ResultCategory, RunStatus, User
from app.security import hash_password
from app.services import pipeline
from app.services.recon.base import AdapterError, AdapterFinding, ReconAdapter


class FakeGoodAdapter(ReconAdapter):
    name = "Fake Good Source"
    modes = frozenset({AccessMode.AUTHORIZED_PASSIVE})

    async def run(self, *, domain, organization_name, timeout):
        return [
            AdapterFinding(
                category=ResultCategory.DNS_NETWORK,
                title=f"Fake record for {domain}",
                summary="1.2.3.4",
                dedupe_key=f"fake:{domain}",
                source_name=self.name,
                source_url=None,
                confidence=1.0,
            )
        ]


class FakeFailingAdapter(ReconAdapter):
    name = "Fake Failing Source"
    modes = frozenset({AccessMode.AUTHORIZED_PASSIVE})

    async def run(self, *, domain, organization_name, timeout):
        raise AdapterError("simulated source outage")


async def test_execute_run_persists_findings_and_marks_completed(db_session, monkeypatch):
    monkeypatch.setattr(pipeline, "ADAPTERS", [FakeGoodAdapter(), FakeFailingAdapter()])

    user = User(email="pipeline-test@example.com", password_hash=hash_password("irrelevant-password-1"))
    org = Organization(name="Pipeline Test Org", primary_domain="pipeline-test.example")
    db_session.add_all([user, org])
    db_session.commit()

    run = ReconRun(
        organization_id=org.id, user_id=user.id, mode=AccessMode.AUTHORIZED_PASSIVE, status=RunStatus.PENDING
    )
    db_session.add(run)
    db_session.commit()
    run_id = run.id

    await pipeline.execute_run(run_id)

    db_session.expire_all()
    refreshed = db_session.get(ReconRun, run_id)
    assert refreshed.status == RunStatus.COMPLETED
    assert refreshed.error_message is not None
    assert "Fake Failing Source" in refreshed.error_message

    results = db_session.query(ReconResult).filter(ReconResult.run_id == run_id).all()
    assert len(results) == 1
    assert results[0].source_name == "Fake Good Source"


async def test_execute_run_skips_when_no_domain(db_session, monkeypatch):
    monkeypatch.setattr(pipeline, "ADAPTERS", [FakeGoodAdapter()])

    user = User(email="pipeline-nodomain@example.com", password_hash=hash_password("irrelevant-password-2"))
    org = Organization(name="No Domain Org", primary_domain=None)
    db_session.add_all([user, org])
    db_session.commit()

    run = ReconRun(
        organization_id=org.id, user_id=user.id, mode=AccessMode.AUTHORIZED_PASSIVE, status=RunStatus.PENDING
    )
    db_session.add(run)
    db_session.commit()
    run_id = run.id

    await pipeline.execute_run(run_id)

    db_session.expire_all()
    refreshed = db_session.get(ReconRun, run_id)
    assert refreshed.status == RunStatus.COMPLETED
    assert db_session.query(ReconResult).filter(ReconResult.run_id == run_id).count() == 0
