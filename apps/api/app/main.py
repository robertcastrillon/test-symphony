from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.exceptions import ChronoTrackException
from app.routers import auth, clients, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="ChronoTrack API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ChronoTrackException)
async def chronotrack_exception_handler(
    request: Request, exc: ChronoTrackException
) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(clients.router)
