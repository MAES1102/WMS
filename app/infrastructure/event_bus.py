"""Synchronous in-memory EventBus used as a transient choreography trigger."""

from app.application.choreography import AdvanceHandler, AdvanceRun
from app.application.errors import StepStateError


class InMemoryRunEventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, AdvanceHandler] = {}

    def subscribe(self, run_id: str, handler: AdvanceHandler) -> None:
        if run_id in self._handlers:
            raise StepStateError(f"Run {run_id!r} already has an advance handler")
        self._handlers[run_id] = handler

    def unsubscribe(self, run_id: str, handler: AdvanceHandler) -> None:
        registered = self._handlers.get(run_id)
        if registered is None:
            return
        if registered is not handler:
            raise StepStateError(
                f"Cannot remove a different handler for run {run_id!r}"
            )
        del self._handlers[run_id]

    def publish(self, event: AdvanceRun) -> None:
        handler = self._handlers.get(event.run_id)
        if handler is None:
            raise StepStateError(
                f"No choreography advance handler for run {event.run_id!r}"
            )
        handler(event)

    def has_subscriber(self, run_id: str) -> bool:
        return run_id in self._handlers

    @property
    def subscriber_count(self) -> int:
        return len(self._handlers)
