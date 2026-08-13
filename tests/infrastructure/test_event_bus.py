import pytest

from app.application.choreography import AdvanceRun
from app.application.errors import StepStateError
from app.infrastructure.event_bus import InMemoryRunEventBus


def test_event_bus_is_run_scoped_and_removes_exact_handler() -> None:
    bus = InMemoryRunEventBus()
    received: list[AdvanceRun] = []
    handler = received.append

    bus.subscribe("run-1", handler)
    bus.publish(AdvanceRun("run-1", 4))

    assert received == [AdvanceRun("run-1", 4)]
    assert bus.has_subscriber("run-1")
    assert bus.subscriber_count == 1

    bus.unsubscribe("run-1", handler)
    assert not bus.has_subscriber("run-1")
    assert bus.subscriber_count == 0


def test_event_bus_rejects_duplicate_or_missing_run_handler() -> None:
    bus = InMemoryRunEventBus()
    handler = lambda _event: None
    bus.subscribe("run-1", handler)

    with pytest.raises(StepStateError, match="already has"):
        bus.subscribe("run-1", handler)
    with pytest.raises(StepStateError, match="No choreography"):
        bus.publish(AdvanceRun("run-2", 1))
    with pytest.raises(StepStateError, match="different handler"):
        bus.unsubscribe("run-1", lambda _event: None)
