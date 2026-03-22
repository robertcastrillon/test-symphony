class ChronoTrackException(Exception):
    """Base exception for ChronoTrack."""

    def __init__(self, message: str = "An unexpected error occurred"):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(ChronoTrackException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class AuthorizationError(ChronoTrackException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Not authorized"):
        super().__init__(message)


class NotFoundError(ChronoTrackException):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message)


class ConflictError(ChronoTrackException):
    """Raised when a resource conflict occurs."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message)


class ValidationError(ChronoTrackException):
    """Raised when validation fails."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message)
