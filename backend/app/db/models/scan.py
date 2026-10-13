"""SQLAlchemy ORM models for persisted scan results (garak + PyRIT).

One `ScanRun` row per completed/failed/cancelled/timed-out scan, either engine,
plus engine-specific child tables. All child tables cascade-delete with their
parent at both the ORM and DB level, so a `ScanRun` can never be left with
orphaned children.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ScanRun(Base):
    """Shared parent row for one scan, from either engine ("garak" | "pyrit")."""

    __tablename__ = "scan_runs"
    __table_args__ = (
        UniqueConstraint("run_id", name="uq_scan_runs_run_id"),
        Index("ix_scan_runs_engine_started_at", "engine", "started_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    engine: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # garak: probe_id / garak_probe populated; pyrit: objective_id / objective populated.
    probe_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    garak_probe: Mapped[str | None] = mapped_column(String(256), nullable=True)
    objective_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)

    ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # garak-only scalar summary fields (denormalized onto the parent for cheap list views).
    attempts_evaluated: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failure_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nli_filtered_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # pyrit-only scalar summary fields.
    outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    outcome_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    achieved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    executed_turns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_score_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Run folder under backend/.scan_runs/, kept for traceability back to raw output files.
    artifact_dir: Mapped[str] = mapped_column(String(512), nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_utcnow, nullable=False)

    findings: Mapped[list["ScanFinding"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", passive_deletes=True
    )
    attack_path_steps: Mapped[list["ScanAttackPathStep"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", passive_deletes=True
    )
    probe_summaries: Mapped[list["ScanProbeSummary"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", passive_deletes=True
    )
    conversation_turns: Mapped[list["ScanConversationTurn"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", passive_deletes=True
    )


class ScanFinding(Base):
    """One row per FailureItem (garak)."""

    __tablename__ = "scan_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("scan_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    probe: Mapped[str] = mapped_column(String(256), nullable=False)
    detector: Mapped[str] = mapped_column(String(256), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    nli_verdict: Mapped[str | None] = mapped_column(String(64), nullable=True)

    run: Mapped["ScanRun"] = relationship(back_populates="findings")


class ScanAttackPathStep(Base):
    """One row per AttackPathStep (garak hitlog): ordinary hits and NLI-filtered
    hits both land here, distinguished by `is_nli_filtered`."""

    __tablename__ = "scan_attack_path_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("scan_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    attempt_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    probe: Mapped[str] = mapped_column(String(256), nullable=False)
    detector: Mapped[str] = mapped_column(String(256), nullable=False)
    prompt_turns: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=False)
    triggers: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    nli_verdict: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_nli_filtered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    run: Mapped["ScanRun"] = relationship(back_populates="attack_path_steps")


class ScanProbeSummary(Base):
    """One row per ProbeSummary (garak per-probe/detector pass tally)."""

    __tablename__ = "scan_probe_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("scan_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    probe: Mapped[str] = mapped_column(String(256), nullable=False)
    detector: Mapped[str] = mapped_column(String(256), nullable=False)
    passed: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)

    run: Mapped["ScanRun"] = relationship(back_populates="probe_summaries")


class ScanConversationTurn(Base):
    """One row per ConversationTurn (pyrit)."""

    __tablename__ = "scan_conversation_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("scan_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    turn: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    run: Mapped["ScanRun"] = relationship(back_populates="conversation_turns")
