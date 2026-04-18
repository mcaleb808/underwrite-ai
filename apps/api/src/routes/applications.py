"""Application intake and status routes."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from src.config import settings
from src.db.models import Application, DecisionRecord, Event, Task, TaskStatus
from src.db.session import get_session, get_session_factory
from src.exceptions import ApplicationValidationError, TaskNotFoundError
from src.schemas.api import (
    ApplicationStatusResponse,
    CreateApplicationResponse,
    DecisionResponse,
)
from src.schemas.applicant import ApplicantProfile
from src.services import event_bus
from src.services.orchestrator import run_task
from src.services.reference import new_reference

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])


async def _save_uploads(task_id: str, files: list[UploadFile]) -> list[str]:
    target_dir = Path(settings.UPLOAD_DIR) / task_id
    target_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for upload in files:
        if not upload.filename:
            continue
        dest = target_dir / Path(upload.filename).name
        dest.write_bytes(await upload.read())
        saved.append(str(dest))
    return saved


@router.post("", response_model=CreateApplicationResponse, status_code=202)
async def create_application(
    request: Request,
    background: BackgroundTasks,
    applicant: Annotated[str, Form()],
    session: Annotated[AsyncSession, Depends(get_session)],
    medical_docs: Annotated[list[UploadFile] | None, File()] = None,
) -> CreateApplicationResponse:
    try:
        profile = ApplicantProfile.model_validate_json(applicant)
    except ValidationError as exc:
        raise ApplicationValidationError(f"invalid applicant: {exc}") from exc

    task_id = uuid.uuid4().hex
    reference = new_reference()
    paths = await _save_uploads(task_id, medical_docs) if medical_docs else []

    existing = (
        await session.execute(
            select(Application).where(Application.applicant_id == profile.applicant_id)
        )
    ).scalar_one_or_none()
    if existing is None:
        existing = Application(
            applicant_id=profile.applicant_id,
            data=profile.model_dump_json(),
        )
        session.add(existing)
        await session.flush()
    else:
        existing.data = profile.model_dump_json()

    task = Task(
        task_id=task_id,
        application_id=existing.id,
        reference_number=reference,
        status=TaskStatus.queued,
    )
    session.add(task)
    await session.commit()

    background.add_task(run_task, task_id, profile, paths)

    return CreateApplicationResponse(
        task_id=task_id,
        reference_number=reference,
        status=TaskStatus.queued.value,
        status_url=str(request.url_for("get_application", task_id=task_id)),
    )


@router.get("/{task_id}", response_model=ApplicationStatusResponse, name="get_application")
async def get_application(
    task_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ApplicationStatusResponse:
    task = (
        await session.execute(
            select(Task).where(Task.task_id == task_id).options(selectinload(Task.decision))
        )
    ).scalar_one_or_none()
    if task is None:
        raise TaskNotFoundError(f"task {task_id} not found")

    decision_payload: DecisionResponse | None = None
    record: DecisionRecord | None = task.decision
    if record is not None:
        decision_payload = DecisionResponse(
            verdict=record.verdict,
            premium_loading_pct=record.premium_loading_pct,
            conditions=json.loads(record.conditions),
            reasoning=record.reasoning,
            citations=json.loads(record.citations),
        )

    return ApplicationStatusResponse(
        task_id=task.task_id,
        reference_number=task.reference_number,
        status=task.status.value,
        risk_score=task.risk_score,
        risk_band=task.risk_band,
        decision=decision_payload,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, default=str)}\n\n"


@router.get("/{task_id}/events")
async def stream_events(
    task_id: str,
    sf: Annotated[async_sessionmaker, Depends(get_session_factory)],
) -> StreamingResponse:
    """SSE stream of graph events. Replays history, then follows live."""

    async def generator():
        async with sf() as session:
            existing_task = (
                await session.execute(select(Task).where(Task.task_id == task_id))
            ).scalar_one_or_none()
            if existing_task is None:
                yield _sse({"node": "orchestrator", "type": "error", "error": "task not found"})
                return

            history = (
                (
                    await session.execute(
                        select(Event).where(Event.task_id == task_id).order_by(Event.id)
                    )
                )
                .scalars()
                .all()
            )
            for row in history:
                yield _sse(
                    {
                        "node": row.node,
                        "type": row.event_type,
                        "payload": json.loads(row.payload),
                        "ts": row.timestamp.isoformat(),
                    }
                )

            # if the task already finished, no live events will arrive
            if existing_task.status in {
                TaskStatus.awaiting_review,
                TaskStatus.approved,
                TaskStatus.modified,
                TaskStatus.sent,
                TaskStatus.failed,
            }:
                yield _sse({"node": "orchestrator", "type": "closed"})
                return

        async for event in event_bus.stream(task_id):
            yield _sse(event)
        yield _sse({"node": "orchestrator", "type": "closed"})

    return StreamingResponse(generator(), media_type="text/event-stream")
