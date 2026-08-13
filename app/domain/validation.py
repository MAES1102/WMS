"""Pure validation of workflow-definition invariants."""

from collections import defaultdict, deque
from dataclasses import dataclass

from app.domain.types import TransitionCondition, WorkflowDefinition


@dataclass(frozen=True)
class ValidationIssue:
    rule: str
    detail: str


class WorkflowDefinitionError(Exception):
    """Complete, deterministic validation failure."""

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues: tuple[ValidationIssue, ...] = tuple(issues)
        summary = "; ".join(f"[{issue.rule}] {issue.detail}" for issue in issues)
        super().__init__(f"{len(issues)} validation issue(s): {summary}")


def validate_workflow_definition(defn: WorkflowDefinition) -> None:
    """Validate all definition rules before run state can be created (FR-006)."""
    issues: list[ValidationIssue] = []
    task_ids = {task.id for task in defn.tasks}

    start_tasks = sorted(
        (task for task in defn.tasks if task.is_start), key=lambda task: task.id
    )
    if not start_tasks:
        issues.append(ValidationIssue("FR-002", "No designated start task"))
    elif len(start_tasks) > 1:
        issues.append(
            ValidationIssue(
                "FR-002",
                f"Multiple designated start tasks: {[task.id for task in start_tasks]}",
            )
        )

    for task in sorted(defn.tasks, key=lambda item: item.id):
        if task.max_attempts < 1:
            issues.append(
                ValidationIssue(
                    "FR-021",
                    f"Task {task.id} ({task.name!r}) has non-positive "
                    f"max_attempts={task.max_attempts}",
                )
            )

    task_counts: dict[int, int] = defaultdict(int)
    for task in defn.tasks:
        task_counts[task.id] += 1
    for task_id, count in sorted(task_counts.items()):
        if count > 1:
            issues.append(
                ValidationIssue(
                    "schema",
                    f"Duplicate task identity {task_id} appears {count} times",
                )
            )

    transitions = sorted(defn.transitions, key=lambda item: item.id)
    for transition in transitions:
        if transition.from_task_id not in task_ids:
            issues.append(
                ValidationIssue(
                    "schema",
                    f"Transition {transition.id}: from_task_id="
                    f"{transition.from_task_id} not in definition",
                )
            )
        if transition.to_task_id not in task_ids:
            issues.append(
                ValidationIssue(
                    "schema",
                    f"Transition {transition.id}: to_task_id="
                    f"{transition.to_task_id} not in definition",
                )
            )
        if transition.from_task_id == transition.to_task_id:
            issues.append(
                ValidationIssue(
                    "FR-005",
                    f"Transition {transition.id} is a self-edge on task "
                    f"{transition.from_task_id}",
                )
            )

    normalized_conditions: dict[int, TransitionCondition] = {}
    for transition in transitions:
        try:
            normalized_conditions[transition.id] = TransitionCondition(
                transition.condition
            )
        except (TypeError, ValueError):
            issues.append(
                ValidationIssue(
                    "FR-007",
                    f"Transition {transition.id} has unsupported condition "
                    f"{transition.condition!r}",
                )
            )

    outgoing: dict[tuple[int, TransitionCondition], list[int]] = defaultdict(list)
    for transition in transitions:
        condition = normalized_conditions.get(transition.id)
        if condition is not None and transition.from_task_id in task_ids:
            outgoing[(transition.from_task_id, condition)].append(transition.id)
    for (task_id, condition), transition_ids in sorted(outgoing.items()):
        if len(transition_ids) > 1:
            issues.append(
                ValidationIssue(
                    "FR-010",
                    f"Task {task_id} has {len(transition_ids)} outgoing "
                    f"{condition.value} transitions {transition_ids}",
                )
            )

    adjacency: dict[int, list[int]] = defaultdict(list)
    for transition in transitions:
        if transition.from_task_id in task_ids and transition.to_task_id in task_ids:
            adjacency[transition.from_task_id].append(transition.to_task_id)

    _detect_cycles(task_ids, adjacency, issues)
    if len(start_tasks) == 1:
        _check_reachability(start_tasks[0].id, task_ids, adjacency, issues)

    if issues:
        raise WorkflowDefinitionError(issues)


def _detect_cycles(
    task_ids: set[int],
    adjacency: dict[int, list[int]],
    issues: list[ValidationIssue],
) -> None:
    white, gray, black = 0, 1, 2
    color = {task_id: white for task_id in task_ids}
    reported: set[int] = set()

    for root in sorted(task_ids):
        if color[root] != white:
            continue

        color[root] = gray
        node_stack = [root]
        path = {root}
        child_indexes = [0]
        neighbours = [sorted(adjacency.get(root, []))]

        while node_stack:
            node = node_stack[-1]
            children = neighbours[-1]
            index = child_indexes[-1]

            if index < len(children):
                child = children[index]
                child_indexes[-1] = index + 1
                child_color = color.get(child, white)

                if child_color == gray and child in path:
                    if child not in reported:
                        issues.append(
                            ValidationIssue(
                                "FR-005",
                                f"Directed cycle revisits task {child}",
                            )
                        )
                        reported.add(child)
                elif child_color == white:
                    color[child] = gray
                    path.add(child)
                    node_stack.append(child)
                    child_indexes.append(0)
                    neighbours.append(sorted(adjacency.get(child, [])))
            else:
                color[node] = black
                path.discard(node)
                node_stack.pop()
                child_indexes.pop()
                neighbours.pop()


def _check_reachability(
    start_id: int,
    task_ids: set[int],
    adjacency: dict[int, list[int]],
    issues: list[ValidationIssue],
) -> None:
    reachable: set[int] = set()
    queue = deque([start_id])

    while queue:
        node = queue.popleft()
        if node in reachable:
            continue
        reachable.add(node)
        for neighbour in sorted(adjacency.get(node, [])):
            if neighbour not in reachable:
                queue.append(neighbour)

    for task_id in sorted(task_ids - reachable):
        issues.append(
            ValidationIssue(
                "FR-004",
                f"Task {task_id} is not reachable from the designated start",
            )
        )

    reachable_terminals = {
        task_id for task_id in reachable if not adjacency.get(task_id)
    }
    if not reachable_terminals:
        issues.append(
            ValidationIssue(
                "FR-003",
                "No reachable terminal task",
            )
        )
