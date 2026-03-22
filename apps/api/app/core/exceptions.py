from fastapi import Request
from fastapi.responses import JSONResponse


class ChronoTrackException(Exception):
    def __init__(self, message: str, status_code: int = 400):
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
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


async def authentication_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def authorization_error_handler(request: Request, exc: AuthorizationError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def not_found_error_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def conflict_error_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
