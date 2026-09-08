from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    MEMBER = "member"
    ADMINISTRATOR = "administrator"


class AccessMode(str, enum.Enum):
    PUBLIC_PROFILE = "public_profile"
    AUTHORIZED_PASSIVE = "authorized_passive"


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResultCategory(str, enum.Enum):
    DOMAINS = "domains"
    WEB_PRESENCE = "web_presence"
    PEOPLE = "people"
    DOCUMENTS = "documents"
    DNS_NETWORK = "dns_network"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.MEMBER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    runs: Mapped[list["ReconRun"]] = relationship(back_populates="user")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    __table_args__ = (UniqueConstraint("name", "primary_domain", name="uq_org_name_domain"),)

    runs: Mapped[list["ReconRun"]] = relationship(back_populates="organization")


class OrganizationMatch(Base):
    """A candidate surfaced by search, before/around user confirmation."""

    __tablename__ = "organization_matches"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    matched_name: Mapped[str] = mapped_column(String(255), nullable=False)
    matched_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(default=0.0, nullable=False)
    rationale: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    searched_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class AuthorizationAcknowledgement(Base):
    __tablename__ = "authorization_acknowledgements"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    user: Mapped["User"] = relationship()
    organization: Mapped["Organization"] = relationship()


class ReconRun(Base):
    __tablename__ = "recon_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    mode: Mapped[AccessMode] = mapped_column(Enum(AccessMode), nullable=False)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.PENDING, nullable=False)
    acknowledgement_id: Mapped[str | None] = mapped_column(
        ForeignKey("authorization_acknowledgements.id"), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="runs")
    user: Mapped["User"] = relationship(back_populates="runs")
    results: Mapped[list["ReconResult"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    notes: Mapped[list["AnalystNote"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class ReconResult(Base):
    __tablename__ = "recon_results"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("recon_runs.id"), nullable=False)
    category: Mapped[ResultCategory] = mapped_column(Enum(ResultCategory), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    confidence: Mapped[float] = mapped_column(default=1.0, nullable=False)
    rationale: Mapped[str | None] = mapped_column(String(500), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hidden_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    run: Mapped["ReconRun"] = relationship(back_populates="results")
    notes: Mapped[list["AnalystNote"]] = relationship(back_populates="result", cascade="all, delete-orphan")


class ResultObservation(Base):
    """Tracks first/last time a given (organization, category, dedupe_key) was observed across runs."""

    __tablename__ = "result_observations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    category: Mapped[ResultCategory] = mapped_column(Enum(ResultCategory), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(500), nullable=False)
    first_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    last_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    last_seen_run_id: Mapped[str] = mapped_column(ForeignKey("recon_runs.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "category", "dedupe_key", name="uq_observation_identity"),
    )


class AnalystNote(Base):
    __tablename__ = "analyst_notes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("recon_runs.id"), nullable=True)
    result_id: Mapped[str | None] = mapped_column(ForeignKey("recon_results.id"), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    run: Mapped["ReconRun | None"] = relationship(back_populates="notes")
    result: Mapped["ReconResult | None"] = relationship(back_populates="notes")
    user: Mapped["User"] = relationship()


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False, index=True)
