"""FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

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
from src.rag.ingest import ensure_seeded
from src.routes.applications import router as applications_router
from src.routes.districts import router as districts_router
from src.routes.health import router as health_router
from src.routes.personas import router as personas_router
from src.services.log import get_logger

log = get_logger(__name__)

_GUIDELINES_PATH = Path(__file__).resolve().parent / "data" / "guidelines.md"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    if settings.OPENAI_API_KEY:
        loop = asyncio.get_running_loop()
        added = await loop.run_in_executor(
            None, ensure_seeded, _GUIDELINES_PATH, settings.CHROMA_DIR
        )
        if added:
            log.info("chroma_seeded", chunks=added, persist_dir=settings.CHROMA_DIR)
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


app.include_router(health_router)
app.include_router(applications_router)
app.include_router(personas_router)
app.include_router(districts_router)
