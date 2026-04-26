"""Domain exceptions - never raise HTTPException outside of routes."""


class UnderwriteError(Exception):
    """Base exception for the underwriting domain."""


class TaskNotFoundError(UnderwriteError):
    pass


class InvalidStateTransitionError(UnderwriteError):
    pass


class ApplicationValidationError(UnderwriteError):
    pass
