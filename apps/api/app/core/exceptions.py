from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ChronoTrackError(Exception):
    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(ChronoTrackError):
    status_code = 404
    detail = "Resource not found"


class ConflictError(ChronoTrackError):
    status_code = 409
    detail = "Resource conflict"


class ValidationError(ChronoTrackError):
    status_code = 422
    detail = "Validation error"


class UnauthorizedError(ChronoTrackError):
    status_code = 401
    detail = "Unauthorized"


class ForbiddenError(ChronoTrackError):
    status_code = 403
    detail = "Forbidden"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ChronoTrackError)
    async def chronotrack_error_handler(
        request: Request, exc: ChronoTrackError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
