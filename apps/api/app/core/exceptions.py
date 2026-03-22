class ChronoTrackException(Exception):
    """Base exception for ChronoTrack application."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(ChronoTrackException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(ChronoTrackException):
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status_code=403)


class NotFoundError(ChronoTrackException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ConflictError(ChronoTrackException):
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


class ValidationError(ChronoTrackException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=422)
