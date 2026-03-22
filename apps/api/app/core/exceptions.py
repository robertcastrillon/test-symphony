class ChronoTrackException(Exception):
    """Base exception for ChronoTrack."""


class AuthenticationError(ChronoTrackException):
    """Raised when authentication fails."""


class AuthorizationError(ChronoTrackException):
    """Raised when a user lacks permission."""


class NotFoundError(ChronoTrackException):
    """Raised when a resource is not found."""


class ConflictError(ChronoTrackException):
    """Raised when a resource already exists."""


class ValidationError(ChronoTrackException):
    """Raised when input validation fails."""
