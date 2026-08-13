"""Bounded workflow-constructor service and persistence-independent contracts."""

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
import re
from typing import Protocol

from app.domain.types import (
    TaskDefinition,
    TaskType,
    TransitionCondition,
    TransitionDefinition,
    WorkflowDefinition,
)
from app.domain.validation import (
    ValidationIssue,
    WorkflowDefinitionError,
    validate_workflow_definition,
)


_TASK_KEY = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


class WorkflowDraftNotFound(LookupError):
    pass


class WorkflowConstructorConflict(RuntimeError):
    pass


class WorkflowDraftRejected(ValueError):
    def __init__(self, issues: tuple[ValidationIssue, ...]) -> None:
        self.issues = issues
        super().__init__("; ".join(f"[{i.rule}] {i.detail}" for i in issues))


class WorkflowActivationRejected(WorkflowDraftRejected):
    pass


@dataclass(frozen=True)
class DraftTaskSpec:
    task_key: str
    name: str
    task_type: str | TaskType
    is_start: bool
    max_attempts: int | None


@dataclass(frozen=True)
class DraftTransitionSpec:
    from_task_key: str
    to_task_key: str
    condition: str | TransitionCondition


@dataclass(frozen=True)
class WorkflowDraftSpec:
    name: str
    tasks: tuple[DraftTaskSpec, ...]
    transitions: tuple[DraftTransitionSpec, ...]


@dataclass(frozen=True)
class StoredWorkflowDraft:
    id: int
    spec: WorkflowDraftSpec
    created_at: datetime
    updated_at: datetime
    latest_revision_number: int | None


@dataclass(frozen=True)
class StoredWorkflowRevision:
    id: int
    draft_id: int
    revision_number: int
    spec: WorkflowDraftSpec
    activated_at: datetime


@dataclass(frozen=True)
class DraftValidationView:
    valid: bool
    issues: tuple[ValidationIssue, ...]


@dataclass(frozen=True)
class WorkflowDraftView:
    id: int
    name: str
    tasks: tuple[DraftTaskSpec, ...]
    transitions: tuple[DraftTransitionSpec, ...]
    created_at: datetime
    updated_at: datetime
    latest_revision_number: int | None
    validation: DraftValidationView


class WorkflowConstructorRepository(Protocol):
    def list_drafts(self) -> tuple[StoredWorkflowDraft, ...]: ...

    def get_draft(self, draft_id: int) -> StoredWorkflowDraft: ...

    def create_draft(
        self,
        spec: WorkflowDraftSpec,
        now: datetime,
    ) -> StoredWorkflowDraft: ...

    def replace_draft(
        self,
        draft_id: int,
        spec: WorkflowDraftSpec,
        now: datetime,
    ) -> StoredWorkflowDraft: ...

    def delete_draft(self, draft_id: int) -> None: ...

    def activate_draft(
        self,
        draft_id: int,
        now: datetime,
    ) -> StoredWorkflowRevision: ...

    def get_revision(self, revision_id: int) -> StoredWorkflowRevision: ...


class WorkflowConstructorService:
    """Manage form-bounded drafts and snapshot valid immutable revisions."""

    def __init__(
        self,
        repository: WorkflowConstructorRepository,
        clock=None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))

    def list_drafts(self) -> tuple[WorkflowDraftView, ...]:
        return tuple(self._view(value) for value in self._repository.list_drafts())

    def get_draft(self, draft_id: int) -> WorkflowDraftView:
        return self._view(self._repository.get_draft(draft_id))

    def create_draft(self, spec: WorkflowDraftSpec) -> WorkflowDraftView:
        normalized = self._normalize_for_storage(spec)
        return self._view(self._repository.create_draft(normalized, self._clock()))

    def replace_draft(
        self,
        draft_id: int,
        spec: WorkflowDraftSpec,
    ) -> WorkflowDraftView:
        normalized = self._normalize_for_storage(spec)
        return self._view(
            self._repository.replace_draft(draft_id, normalized, self._clock())
        )

    def delete_draft(self, draft_id: int) -> None:
        self._repository.delete_draft(draft_id)

    def validate_draft(self, draft_id: int) -> DraftValidationView:
        return self._validation(self._repository.get_draft(draft_id).spec)

    def validate_spec(self, spec: WorkflowDraftSpec) -> DraftValidationView:
        return self._validation(spec)

    def activate_draft(self, draft_id: int) -> StoredWorkflowRevision:
        stored = self._repository.get_draft(draft_id)
        validation = self._validation(stored.spec)
        if not validation.valid:
            raise WorkflowActivationRejected(validation.issues)
        return self._repository.activate_draft(draft_id, self._clock())

    def get_revision(self, revision_id: int) -> StoredWorkflowRevision:
        return self._repository.get_revision(revision_id)

    def _view(self, stored: StoredWorkflowDraft) -> WorkflowDraftView:
        return WorkflowDraftView(
            id=stored.id,
            name=stored.spec.name,
            tasks=stored.spec.tasks,
            transitions=stored.spec.transitions,
            created_at=stored.created_at,
            updated_at=stored.updated_at,
            latest_revision_number=stored.latest_revision_number,
            validation=self._validation(stored.spec),
        )

    def _normalize_for_storage(self, spec: WorkflowDraftSpec) -> WorkflowDraftSpec:
        validation = self._validation(spec)
        fatal_rules = {"FR-007", "FR-010", "FR-021", "FR-048", "FR-049", "FR-050"}
        fatal = tuple(issue for issue in validation.issues if issue.rule in fatal_rules)
        if fatal:
            raise WorkflowDraftRejected(fatal)
        return WorkflowDraftSpec(
            name=spec.name.strip(),
            tasks=tuple(
                DraftTaskSpec(
                    task_key=task.task_key.strip(),
                    name=task.name.strip(),
                    task_type=TaskType(task.task_type),
                    is_start=task.is_start,
                    max_attempts=task.max_attempts,
                )
                for task in spec.tasks
            ),
            transitions=tuple(
                DraftTransitionSpec(
                    from_task_key=item.from_task_key.strip(),
                    to_task_key=item.to_task_key.strip(),
                    condition=TransitionCondition(item.condition),
                )
                for item in spec.transitions
            ),
        )

    @classmethod
    def _validation(cls, spec: WorkflowDraftSpec) -> DraftValidationView:
        issues = cls._field_issues(spec)
        issues.extend(cls._domain_issues(spec))
        unique: list[ValidationIssue] = []
        seen: set[tuple[str, str]] = set()
        for issue in issues:
            identity = (issue.rule, issue.detail)
            if identity not in seen:
                seen.add(identity)
                unique.append(issue)
        return DraftValidationView(not unique, tuple(unique))

    @staticmethod
    def _field_issues(spec: WorkflowDraftSpec) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        name = spec.name.strip() if isinstance(spec.name, str) else ""
        if not 1 <= len(name) <= 120:
            issues.append(
                ValidationIssue("FR-048", "Draft name must contain 1–120 characters")
            )

        keys: list[str] = []
        for index, task in enumerate(spec.tasks, start=1):
            key = task.task_key.strip() if isinstance(task.task_key, str) else ""
            keys.append(key)
            if not _TASK_KEY.fullmatch(key):
                issues.append(
                    ValidationIssue(
                        "FR-050",
                        f"Task {index} key must match {_TASK_KEY.pattern!r}",
                    )
                )
            task_name = task.name.strip() if isinstance(task.name, str) else ""
            if not 1 <= len(task_name) <= 120:
                issues.append(
                    ValidationIssue(
                        "FR-050",
                        f"Task {key or index!r} name must contain 1–120 characters",
                    )
                )
            try:
                task_type = TaskType(task.task_type)
            except (TypeError, ValueError):
                task_type = None
            if task_type is TaskType.HUMAN_APPROVAL and task.max_attempts is not None:
                issues.append(
                    ValidationIssue(
                        "FR-050",
                        f"Human task {key!r} must not define max_attempts",
                    )
                )

        for key, count in sorted(Counter(keys).items()):
            if count > 1:
                issues.append(
                    ValidationIssue(
                        "FR-050",
                        f"Task key {key!r} occurs {count} times",
                    )
                )

        known = set(keys)
        for index, transition in enumerate(spec.transitions, start=1):
            source = transition.from_task_key.strip()
            target = transition.to_task_key.strip()
            if source not in known:
                issues.append(
                    ValidationIssue(
                        "FR-050",
                        f"Transition {index} source {source!r} is not a task key",
                    )
                )
            if target not in known:
                issues.append(
                    ValidationIssue(
                        "FR-050",
                        f"Transition {index} target {target!r} is not a task key",
                    )
                )
            if source == target:
                issues.append(
                    ValidationIssue(
                        "FR-050",
                        f"Transition {index} cannot connect task {source!r} to itself",
                    )
                )
        return issues

    @staticmethod
    def _domain_issues(spec: WorkflowDraftSpec) -> list[ValidationIssue]:
        first_id_by_key: dict[str, int] = {}
        tasks: list[TaskDefinition] = []
        for task_id, task in enumerate(spec.tasks, start=1):
            key = task.task_key.strip()
            first_id_by_key.setdefault(key, task_id)
            tasks.append(
                TaskDefinition(
                    id=task_id,
                    name=task.name,
                    task_type=task.task_type,
                    is_start=task.is_start,
                    max_attempts=task.max_attempts,
                )
            )

        transitions: list[TransitionDefinition] = []
        for transition_id, item in enumerate(spec.transitions, start=1):
            source = first_id_by_key.get(item.from_task_key.strip())
            target = first_id_by_key.get(item.to_task_key.strip())
            if source is None or target is None:
                continue
            transitions.append(
                TransitionDefinition(
                    id=transition_id,
                    from_task_id=source,
                    to_task_id=target,
                    condition=item.condition,
                )
            )

        try:
            validate_workflow_definition(
                WorkflowDefinition(0, tuple(tasks), tuple(transitions))
            )
        except WorkflowDefinitionError as exc:
            return list(exc.issues)
        return []
