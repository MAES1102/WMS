"""Shared application-state errors."""


class StepStateError(RuntimeError):
    pass


class StateVersionConflict(StepStateError):
    pass
