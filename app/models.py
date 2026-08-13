from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('RUNNING','COMPLETED','FAILED')",
            name="ck_run_status",
        ),
        CheckConstraint(
            "mode IN ('orchestration','choreography')",
            name="ck_run_mode",
        ),
        CheckConstraint(
            "scenario_name IS NULL OR scenario_name IN "
            "('success','retry_then_success','permanent_failure')",
            name="ck_run_scenario_name",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="RUNNING")
    # Nullable until C5B switches execution routes to deterministic scenarios.
    scenario_name: Mapped[str | None] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING','RUNNING','DONE','FAILED')",
            name="ck_task_status",
        ),
        CheckConstraint(
            "max_attempts >= 1",
            name="ck_task_max_attempts",
        ),
        UniqueConstraint("workflow_id", "order", name="uq_task_workflow_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id"), nullable=False
    )
    # Retained for definition display ordering, not transition resolution.
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_start: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Temporary compatibility fields until C5B moves execution state to TaskAttempt.
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="PENDING"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )


class WorkflowTransition(Base):
    """Directed conditional edge between two task definitions.

    Domain validation ensures that both endpoints belong to the same workflow;
    simple foreign keys cannot enforce that cross-row invariant.
    """

    __tablename__ = "workflow_transitions"
    __table_args__ = (
        CheckConstraint(
            "condition IN ('SUCCESS','FAILURE','ALWAYS')",
            name="ck_wt_condition",
        ),
        CheckConstraint(
            "from_task_id != to_task_id",
            name="ck_wt_no_self_edge",
        ),
        UniqueConstraint(
            "workflow_id", "from_task_id", "condition",
            name="uq_wt_workflow_source_condition",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id"), nullable=False
    )
    from_task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id"), nullable=False
    )
    to_task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id"), nullable=False
    )
    condition: Mapped[str] = mapped_column(String, nullable=False)


class TaskAttempt(Base):
    """One execution attempt of a task within a run."""

    __tablename__ = "task_attempts"
    __table_args__ = (
        CheckConstraint(
            "attempt_ordinal >= 1",
            name="ck_attempt_ordinal",
        ),
        CheckConstraint(
            "outcome IN ('SUCCESS','FAILURE')",
            name="ck_attempt_outcome",
        ),
        UniqueConstraint(
            "run_id", "task_id", "attempt_ordinal",
            name="uq_attempt_run_task_ordinal",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_runs.id"), nullable=False
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id"), nullable=False
    )
    attempt_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class TraceEntry(Base):
    """One run-local ordered execution observation."""

    __tablename__ = "trace_entries"
    __table_args__ = (
        CheckConstraint(
            "position >= 1",
            name="ck_trace_position",
        ),
        CheckConstraint(
            "attempt_ordinal IS NULL OR attempt_ordinal >= 1",
            name="ck_trace_attempt_ordinal",
        ),
        CheckConstraint(
            "observation_kind IN ("
            "'RUN_STARTED','ATTEMPT_OUTCOME','RETRY_OBSERVATION',"
            "'TRANSITION_SELECTED','SUCCESSFUL_TERMINAL','UNSUCCESSFUL_TERMINAL',"
            "'CONTROLLED_EXECUTION_ERROR'"
            ")",
            name="ck_trace_kind",
        ),
        CheckConstraint(
            "outcome IS NULL OR outcome IN ('SUCCESS','FAILURE')",
            name="ck_trace_outcome",
        ),
        UniqueConstraint("run_id", "position", name="uq_trace_run_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_runs.id"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    observation_kind: Mapped[str] = mapped_column(String, nullable=False)
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id"), nullable=True
    )
    attempt_ordinal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String, nullable=True)
    transition_id: Mapped[int | None] = mapped_column(
        ForeignKey("workflow_transitions.id"), nullable=True
    )
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
