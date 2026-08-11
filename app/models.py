from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # unique → нет дублей, целостность на уровне БД
    password: Mapped[str] = mapped_column(String, nullable=False)


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)  # FK: связь с владельцем


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    # CheckConstraint: валидные статусы гарантирует БД, не только код
    __table_args__ = (
        CheckConstraint(
            "status IN ('RUNNING','COMPLETED','FAILED')",
            name="ck_run_status",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="RUNNING")
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # nullable so existing rows survive; populated on new runs
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING','RUNNING','DONE','FAILED')",
            name="ck_task_status",
        ),
        # уникальный order внутри workflow → детерминированный порядок выполнения
        # Kept for backward compatibility with the legacy sequential executor.
        UniqueConstraint("workflow_id", "order", name="uq_task_workflow_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id"), nullable=False
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    # Deprecated: kept for legacy execution compatibility.
    # Runtime state moved to TaskExecution.
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="PENDING"
    )
    # Deprecated: kept for legacy execution compatibility.
    # Runtime state moved to TaskExecution.
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    # Deprecated: kept for legacy execution compatibility.
    # Runtime state moved to TaskExecution.
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )


class TaskExecution(Base):
    """Runtime state for a single task within a specific WorkflowRun.

    Separates execution instance from workflow definition (Task).
    One Task definition can have many TaskExecution records across runs.
    """

    __tablename__ = "task_executions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING','RUNNING','DONE','FAILED')",
            name="ck_task_exec_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_runs.id"), nullable=False
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# Condition under which a WorkflowTransition edge is followed after a task
# finishes executing.  ALWAYS is used for unconditional edges (e.g. after a
# join) and lets the graph degrade gracefully when only one outcome matters.
TRANSITION_CONDITIONS = ("SUCCESS", "FAILURE", "ALWAYS")


class WorkflowTransition(Base):
    """A directed edge of the workflow graph: from_task --condition--> to_task.

    This is what turns the system from a linear task list into a BPMN-like
    graph: a task can have multiple outgoing edges (decision gateway), and
    edges may point backwards to an earlier task (retry loop).
    """

    __tablename__ = "workflow_transitions"
    __table_args__ = (
        CheckConstraint(
            "condition IN ('SUCCESS','FAILURE','ALWAYS')",
            name="ck_transition_condition",
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
    condition: Mapped[str] = mapped_column(String, nullable=False, default="ALWAYS")
    # lower number = higher priority; used to pick among several edges that
    # share the same (from_task_id, condition) pair.
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
