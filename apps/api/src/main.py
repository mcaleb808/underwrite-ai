"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.db.models import Base
from src.db.session import engine
from src.exceptions import (
    ApplicationValidationError,
    InvalidStateTransitionError,
    TaskNotFoundError,
)
from src.routes.applications import router as applications_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="UnderwriteAI",
    description="AI-powered health insurance underwriting API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.WEB_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InvalidStateTransitionError)
async def invalid_transition_handler(
    request: Request, exc: InvalidStateTransitionError
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ApplicationValidationError)
async def validation_error_handler(
    request: Request, exc: ApplicationValidationError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(applications_router)
