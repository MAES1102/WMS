"""SQLAlchemy adapter for bounded draft CRUD and immutable activation."""

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.constructor import (
    DraftTaskSpec,
    DraftTransitionSpec,
    StoredWorkflowDraft,
    StoredWorkflowRevision,
    WorkflowConstructorConflict,
    WorkflowDraftNotFound,
    WorkflowDraftSpec,
)
from app.domain.types import TaskType, TransitionCondition
from app.persistence.models import (
    DraftTask,
    DraftTransition,
    RevisionTask,
    RevisionTransition,
    WorkflowDraft,
    WorkflowRevision,
)


class SqlAlchemyWorkflowConstructorRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_drafts(self) -> tuple[StoredWorkflowDraft, ...]:
        rows = self._session.scalars(
            select(WorkflowDraft).order_by(WorkflowDraft.id)
        ).all()
        return tuple(self._draft_record(row) for row in rows)

    def get_draft(self, draft_id: int) -> StoredWorkflowDraft:
        return self._draft_record(self._draft_row(draft_id))

    def create_draft(
        self,
        spec: WorkflowDraftSpec,
        now,
    ) -> StoredWorkflowDraft:
        row = WorkflowDraft(name=spec.name, created_at=now, updated_at=now)
        try:
            self._session.add(row)
            self._session.flush()
            self._replace_content(row.id, spec)
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise WorkflowConstructorConflict(
                "Draft content conflicts with persisted constraints"
            ) from exc
        except BaseException:
            self._session.rollback()
            raise
        return self.get_draft(row.id)

    def replace_draft(
        self,
        draft_id: int,
        spec: WorkflowDraftSpec,
        now,
    ) -> StoredWorkflowDraft:
        row = self._draft_row(draft_id)
        try:
            self._session.execute(
                delete(DraftTransition).where(DraftTransition.draft_id == draft_id)
            )
            self._session.execute(
                delete(DraftTask).where(DraftTask.draft_id == draft_id)
            )
            row.name = spec.name
            row.updated_at = now
            self._session.flush()
            self._replace_content(draft_id, spec)
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise WorkflowConstructorConflict(
                "Draft update conflicts with persisted constraints"
            ) from exc
        except BaseException:
            self._session.rollback()
            raise
        return self.get_draft(draft_id)

    def delete_draft(self, draft_id: int) -> None:
        row = self._draft_row(draft_id)
        revision_count = self._session.scalar(
            select(func.count())
            .select_from(WorkflowRevision)
            .where(WorkflowRevision.draft_id == draft_id)
        )
        if revision_count:
            raise WorkflowConstructorConflict(
                "A draft with activated revision history cannot be deleted"
            )
        try:
            self._session.execute(
                delete(DraftTransition).where(DraftTransition.draft_id == draft_id)
            )
            self._session.execute(
                delete(DraftTask).where(DraftTask.draft_id == draft_id)
            )
            self._session.delete(row)
            self._session.commit()
        except BaseException:
            self._session.rollback()
            raise

    def activate_draft(self, draft_id: int, now) -> StoredWorkflowRevision:
        draft = self._draft_row(draft_id)
        latest = self._latest_revision_number(draft_id) or 0
        revision = WorkflowRevision(
            draft_id=draft_id,
            revision_number=latest + 1,
            name=draft.name,
            activated_at=now,
        )
        try:
            self._session.add(revision)
            self._session.flush()
            draft_tasks = self._draft_tasks(draft_id)
            revision_task_by_draft_id: dict[int, RevisionTask] = {}
            for task in draft_tasks:
                copied = RevisionTask(
                    revision_id=revision.id,
                    task_key=task.task_key,
                    name=task.name,
                    task_type=task.task_type,
                    is_start=task.is_start,
                    max_attempts=task.max_attempts,
                )
                self._session.add(copied)
                self._session.flush()
                revision_task_by_draft_id[task.id] = copied

            for transition in self._draft_transitions(draft_id):
                self._session.add(
                    RevisionTransition(
                        revision_id=revision.id,
                        from_task_id=revision_task_by_draft_id[
                            transition.from_task_id
                        ].id,
                        to_task_id=revision_task_by_draft_id[
                            transition.to_task_id
                        ].id,
                        condition=transition.condition,
                    )
                )
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise WorkflowConstructorConflict(
                "Draft activation conflicts with persisted revision state"
            ) from exc
        except BaseException:
            self._session.rollback()
            raise
        return self.get_revision(revision.id)

    def get_revision(self, revision_id: int) -> StoredWorkflowRevision:
        revision = self._session.get(WorkflowRevision, revision_id)
        if revision is None:
            raise WorkflowDraftNotFound(
                f"Workflow revision {revision_id} does not exist"
            )
        tasks = self._session.scalars(
            select(RevisionTask)
            .where(RevisionTask.revision_id == revision_id)
            .order_by(RevisionTask.id)
        ).all()
        transitions = self._session.scalars(
            select(RevisionTransition)
            .where(RevisionTransition.revision_id == revision_id)
            .order_by(RevisionTransition.id)
        ).all()
        key_by_id = {task.id: task.task_key for task in tasks}
        return StoredWorkflowRevision(
            id=revision.id,
            draft_id=revision.draft_id,
            revision_number=revision.revision_number,
            spec=WorkflowDraftSpec(
                name=revision.name,
                tasks=tuple(self._task_spec(task) for task in tasks),
                transitions=tuple(
                    DraftTransitionSpec(
                        from_task_key=key_by_id[item.from_task_id],
                        to_task_key=key_by_id[item.to_task_id],
                        condition=TransitionCondition(item.condition),
                    )
                    for item in transitions
                ),
            ),
            activated_at=revision.activated_at,
        )

    def _draft_row(self, draft_id: int) -> WorkflowDraft:
        row = self._session.get(WorkflowDraft, draft_id)
        if row is None:
            raise WorkflowDraftNotFound(f"Workflow draft {draft_id} does not exist")
        return row

    def _draft_record(self, row: WorkflowDraft) -> StoredWorkflowDraft:
        tasks = self._draft_tasks(row.id)
        transitions = self._draft_transitions(row.id)
        key_by_id = {task.id: task.task_key for task in tasks}
        return StoredWorkflowDraft(
            id=row.id,
            spec=WorkflowDraftSpec(
                name=row.name,
                tasks=tuple(self._task_spec(task) for task in tasks),
                transitions=tuple(
                    DraftTransitionSpec(
                        from_task_key=key_by_id[item.from_task_id],
                        to_task_key=key_by_id[item.to_task_id],
                        condition=TransitionCondition(item.condition),
                    )
                    for item in transitions
                ),
            ),
            created_at=row.created_at,
            updated_at=row.updated_at,
            latest_revision_number=self._latest_revision_number(row.id),
        )

    def _replace_content(self, draft_id: int, spec: WorkflowDraftSpec) -> None:
        task_by_key: dict[str, DraftTask] = {}
        for item in spec.tasks:
            row = DraftTask(
                draft_id=draft_id,
                task_key=item.task_key,
                name=item.name,
                task_type=TaskType(item.task_type).value,
                is_start=item.is_start,
                max_attempts=item.max_attempts,
            )
            self._session.add(row)
            self._session.flush()
            task_by_key[item.task_key] = row
        for item in spec.transitions:
            self._session.add(
                DraftTransition(
                    draft_id=draft_id,
                    from_task_id=task_by_key[item.from_task_key].id,
                    to_task_id=task_by_key[item.to_task_key].id,
                    condition=TransitionCondition(item.condition).value,
                )
            )

    def _draft_tasks(self, draft_id: int) -> list[DraftTask]:
        return list(
            self._session.scalars(
                select(DraftTask)
                .where(DraftTask.draft_id == draft_id)
                .order_by(DraftTask.id)
            ).all()
        )

    def _draft_transitions(self, draft_id: int) -> list[DraftTransition]:
        return list(
            self._session.scalars(
                select(DraftTransition)
                .where(DraftTransition.draft_id == draft_id)
                .order_by(DraftTransition.id)
            ).all()
        )

    def _latest_revision_number(self, draft_id: int) -> int | None:
        return self._session.scalar(
            select(func.max(WorkflowRevision.revision_number)).where(
                WorkflowRevision.draft_id == draft_id
            )
        )

    @staticmethod
    def _task_spec(row: DraftTask | RevisionTask) -> DraftTaskSpec:
        return DraftTaskSpec(
            task_key=row.task_key,
            name=row.name,
            task_type=TaskType(row.task_type),
            is_start=row.is_start,
            max_attempts=row.max_attempts,
        )
