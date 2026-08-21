"""Persistence model for workflow definitions, purchase_request runs, and audit data."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.database import Base


TASK_TYPES = (
    "'REQUEST_VALIDATION','HUMAN_APPROVAL',"
    "'PURCHASE_AUTHORIZATION','CREATE_NOTIFICATION'"
)
TRANSITION_CONDITIONS = "'SUCCESS','FAILURE','ALWAYS'"
WORKFLOW_STATES = (
    "'SUBMITTED','VALIDATION_FAILED','PENDING_APPROVAL','APPROVED',"
    "'REJECTED','AUTHORIZED','NEEDS_MANUAL_ACTION'"
)
TRACE_KINDS = (
    "'RUN_STARTED','ATTEMPT_OUTCOME','RETRY_OBSERVATION',"
    "'TRANSITION_SELECTED','WAITING_FOR_APPROVAL','RUN_RESUMED',"
    "'APPROVAL_DECIDED','WORKFLOW_STATE_CHANGED','NOTIFICATION_CREATED',"
    "'SUCCESSFUL_TERMINAL','UNSUCCESSFUL_TERMINAL',"
    "'CONTROLLED_EXECUTION_ERROR'"
)


class WorkflowDraft(Base):
    __tablename__ = "purchase_request_workflow_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class DraftTask(Base):
    __tablename__ = "purchase_request_draft_tasks"
    __table_args__ = (
        CheckConstraint(
            f"task_type IN ({TASK_TYPES})",
            name="ck_purchase_request_draft_task_type",
        ),
        CheckConstraint(
            "(task_type = 'HUMAN_APPROVAL' AND max_attempts IS NULL) OR "
            "(task_type != 'HUMAN_APPROVAL' AND max_attempts >= 1)",
            name="ck_purchase_request_draft_task_attempt_bound",
        ),
        UniqueConstraint(
            "draft_id", "task_key", name="uq_purchase_request_draft_task_key"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    draft_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_request_workflow_drafts.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_start: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)


class DraftTransition(Base):
    __tablename__ = "purchase_request_draft_transitions"
    __table_args__ = (
        CheckConstraint(
            f"condition IN ({TRANSITION_CONDITIONS})",
            name="ck_purchase_request_draft_transition_condition",
        ),
        CheckConstraint(
            "from_task_id != to_task_id",
            name="ck_purchase_request_draft_transition_no_self_edge",
        ),
        UniqueConstraint(
            "draft_id",
            "from_task_id",
            "condition",
            name="uq_purchase_request_draft_transition_precedence",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    draft_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_request_workflow_drafts.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_task_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_request_draft_tasks.id", ondelete="CASCADE"), nullable=False
    )
    to_task_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_request_draft_tasks.id", ondelete="CASCADE"), nullable=False
    )
    condition: Mapped[str] = mapped_column(String(16), nullable=False)


class WorkflowRevision(Base):
    __tablename__ = "purchase_request_workflow_revisions"
    __table_args__ = (
        CheckConstraint("revision_number >= 1", name="ck_purchase_request_revision_number"),
        UniqueConstraint(
            "draft_id", "revision_number", name="uq_purchase_request_draft_revision"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    draft_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_request_workflow_drafts.id"), nullable=False
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    activated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class RevisionTask(Base):
    __tablename__ = "purchase_request_revision_tasks"
    __table_args__ = (
        CheckConstraint(
            f"task_type IN ({TASK_TYPES})",
            name="ck_purchase_request_revision_task_type",
        ),
        CheckConstraint(
            "(task_type = 'HUMAN_APPROVAL' AND max_attempts IS NULL) OR "
            "(task_type != 'HUMAN_APPROVAL' AND max_attempts >= 1)",
            name="ck_purchase_request_revision_task_attempt_bound",
        ),
        UniqueConstraint(
            "revision_id", "task_key", name="uq_purchase_request_revision_task_key"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    revision_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_request_workflow_revisions.id"), nullable=False
    )
    task_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_start: Mapped[bool] = mapped_column(Boolean, nullable=False)
    max_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)


class RevisionTransition(Base):
    __tablename__ = "purchase_request_revision_transitions"
    __table_args__ = (
        CheckConstraint(
            f"condition IN ({TRANSITION_CONDITIONS})",
            name="ck_purchase_request_revision_transition_condition",
        ),
        CheckConstraint(
            "from_task_id != to_task_id",
            name="ck_purchase_request_revision_transition_no_self_edge",
        ),
        UniqueConstraint(
            "revision_id",
            "from_task_id",
            "condition",
            name="uq_purchase_request_revision_transition_precedence",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    revision_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_request_workflow_revisions.id"), nullable=False
    )
    from_task_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_request_revision_tasks.id"), nullable=False
    )
    to_task_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_request_revision_tasks.id"), nullable=False
    )
    condition: Mapped[str] = mapped_column(String(16), nullable=False)


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"
    __table_args__ = (
        CheckConstraint(
            f"state IN ({WORKFLOW_STATES})", name="ck_purchase_request_state"
        ),
        CheckConstraint(
            "amount IS NULL OR (amount > 0 AND amount <= 999999999.99)",
            name="ck_purchase_request_amount_range",
        ),
        CheckConstraint(
            "currency IS NULL OR "
            "(length(currency) = 3 AND currency = upper(currency))",
            name="ck_purchase_request_currency",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    requester_name_raw: Mapped[str] = mapped_column(String(512), nullable=False)
    department_raw: Mapped[str] = mapped_column(String(512), nullable=False)
    item_or_service_raw: Mapped[str] = mapped_column(String(1024), nullable=False)
    supplier_raw: Mapped[str] = mapped_column(String(512), nullable=False)
    amount_raw: Mapped[str] = mapped_column(String(32), nullable=False)
    currency_raw: Mapped[str] = mapped_column(String(16), nullable=False)
    business_justification_raw: Mapped[str] = mapped_column(String(2000), nullable=False)
    required_date_raw: Mapped[str] = mapped_column(String(32), nullable=False)
    requester_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    item_or_service: Mapped[str | None] = mapped_column(String(200), nullable=True)
    supplier: Mapped[str | None] = mapped_column(String(120), nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(11, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    business_justification: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    required_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class PurchaseRequestWorkflowRun(Base):
    __tablename__ = "purchase_request_workflow_runs"
    __table_args__ = (
        CheckConstraint(
            "mode IN ('orchestration','choreography')",
            name="ck_purchase_request_run_mode",
        ),
        CheckConstraint(
            "scenario IN ('standard','retry_then_success','authorization_unavailable')",
            name="ck_purchase_request_run_scenario",
        ),
        CheckConstraint(
            "status IN ('RUNNING','WAITING_FOR_APPROVAL','COMPLETED','FAILED')",
            name="ck_purchase_request_run_status",
        ),
        CheckConstraint(
            "(status IN ('RUNNING','WAITING_FOR_APPROVAL') AND finished_at IS NULL) "
            "OR (status IN ('COMPLETED','FAILED') AND finished_at IS NOT NULL)",
            name="ck_purchase_request_run_finished_consistency",
        ),
        UniqueConstraint("purchase_request_id", name="uq_purchase_request_run_purchase_request"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    purchase_request_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_requests.id"), nullable=False
    )
    revision_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_request_workflow_revisions.id"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    scenario: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ExecutionCursor(Base):
    __tablename__ = "purchase_request_execution_cursors"
    __table_args__ = (
        CheckConstraint(
            "phase IN ('READY','WAITING_FOR_APPROVAL','TERMINAL')",
            name="ck_purchase_request_cursor_phase",
        ),
        CheckConstraint(
            "state_version >= 1", name="ck_purchase_request_cursor_state_version"
        ),
        CheckConstraint(
            "terminal_decision IS NULL OR terminal_decision IN "
            "('SUCCESSFUL_TERMINAL','UNSUCCESSFUL_TERMINAL')",
            name="ck_purchase_request_cursor_terminal_decision",
        ),
        CheckConstraint(
            "(phase = 'TERMINAL' AND terminal_decision IS NOT NULL) OR "
            "(phase != 'TERMINAL' AND terminal_decision IS NULL)",
            name="ck_purchase_request_cursor_terminal_consistency",
        ),
    )

    run_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_request_workflow_runs.id"), primary_key=True
    )
    current_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchase_request_revision_tasks.id"), nullable=True
    )
    phase: Mapped[str] = mapped_column(String(32), nullable=False)
    state_version: Mapped[int] = mapped_column(Integer, nullable=False)
    terminal_decision: Mapped[str | None] = mapped_column(String(32), nullable=True)


class PurchaseRequestTaskAttempt(Base):
    __tablename__ = "purchase_request_task_attempts"
    __table_args__ = (
        CheckConstraint("attempt_ordinal >= 1", name="ck_purchase_request_attempt_ordinal"),
        CheckConstraint(
            "outcome IN ('SUCCESS','FAILURE')", name="ck_purchase_request_attempt_outcome"
        ),
        CheckConstraint(
            "failure_class IS NULL OR failure_class IN "
            "('BUSINESS','RETRYABLE_TECHNICAL','NON_RETRYABLE_TECHNICAL')",
            name="ck_purchase_request_attempt_failure_class",
        ),
        CheckConstraint(
            "(outcome = 'SUCCESS' AND failure_class IS NULL) OR "
            "(outcome = 'FAILURE' AND failure_class IS NOT NULL)",
            name="ck_purchase_request_attempt_result_consistency",
        ),
        CheckConstraint(
            "finished_at >= started_at", name="ck_purchase_request_attempt_time_order"
        ),
        UniqueConstraint(
            "run_id",
            "task_id",
            "attempt_ordinal",
            name="uq_purchase_request_attempt_run_task_ordinal",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_request_workflow_runs.id"), nullable=False
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_request_revision_tasks.id"), nullable=False
    )
    attempt_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    failure_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ApprovalWorkItem(Base):
    __tablename__ = "purchase_request_approval_work_items"
    __table_args__ = (
        CheckConstraint(
            "state IN ('PENDING','APPROVED','REJECTED')",
            name="ck_purchase_request_work_item_state",
        ),
        CheckConstraint(
            "(state = 'PENDING' AND decided_at IS NULL) OR "
            "(state IN ('APPROVED','REJECTED') AND decided_at IS NOT NULL)",
            name="ck_purchase_request_work_item_decided_consistency",
        ),
        UniqueConstraint(
            "run_id", "task_id", name="uq_purchase_request_work_item_run_task"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_request_workflow_runs.id"), nullable=False
    )
    purchase_request_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_requests.id"), nullable=False
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_request_revision_tasks.id"), nullable=False
    )
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ApprovalDecision(Base):
    __tablename__ = "purchase_request_approval_decisions"
    __table_args__ = (
        CheckConstraint(
            "decision IN ('APPROVE','REJECT')",
            name="ck_purchase_request_decision_value",
        ),
        CheckConstraint(
            "(decision = 'APPROVE' AND reason IS NULL AND "
            "(note IS NULL OR length(note) <= 500)) OR "
            "(decision = 'REJECT' AND note IS NULL AND "
            "length(trim(reason)) BETWEEN 1 AND 500)",
            name="ck_purchase_request_decision_payload",
        ),
        UniqueConstraint("work_item_id", name="uq_purchase_request_work_item_decision"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    work_item_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_request_approval_work_items.id"), nullable=False
    )
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class PurchaseAuthorization(Base):
    __tablename__ = "purchase_request_authorization_records"
    __table_args__ = (
        UniqueConstraint("purchase_request_id", name="uq_purchase_request_authorization_purchase_request"),
        UniqueConstraint("run_id", name="uq_purchase_request_authorization_run"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    purchase_request_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_requests.id"), nullable=False
    )
    run_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_request_workflow_runs.id"), nullable=False
    )
    authorization_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    authorized_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class InternalNotification(Base):
    __tablename__ = "purchase_request_internal_notifications"
    __table_args__ = (
        UniqueConstraint("run_id", name="uq_purchase_request_notification_run"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    purchase_request_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_requests.id"), nullable=False
    )
    run_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_request_workflow_runs.id"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class PurchaseRequestTraceEntry(Base):
    __tablename__ = "purchase_request_trace_entries"
    __table_args__ = (
        CheckConstraint("position >= 1", name="ck_purchase_request_trace_position"),
        CheckConstraint(
            "attempt_ordinal IS NULL OR attempt_ordinal >= 1",
            name="ck_purchase_request_trace_attempt_ordinal",
        ),
        CheckConstraint(
            f"observation_kind IN ({TRACE_KINDS})",
            name="ck_purchase_request_trace_kind",
        ),
        UniqueConstraint(
            "run_id", "position", name="uq_purchase_request_trace_run_position"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("purchase_request_workflow_runs.id"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    observation_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchase_request_revision_tasks.id"), nullable=True
    )
    attempt_ordinal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)


def _reject_revision_mutation(_mapper, _connection, target) -> None:
    raise ValueError(
        f"Activated workflow revision content is immutable: {type(target).__name__}"
    )


for _revision_model in (WorkflowRevision, RevisionTask, RevisionTransition):
    event.listen(_revision_model, "before_update", _reject_revision_mutation)
    event.listen(_revision_model, "before_delete", _reject_revision_mutation)
