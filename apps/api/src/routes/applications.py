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
from src.exceptions import (
    ApplicationValidationError,
    InvalidStateTransitionError,
    TaskNotFoundError,
)
from src.schemas.api import (
    ApplicationStatusResponse,
    ApproveRequest,
    ApproveResponse,
    CreateApplicationResponse,
    DecisionResponse,
    ModifyDecisionRequest,
    ReevalRequest,
    ReevalResponse,
)
from src.schemas.applicant import ApplicantProfile
from src.schemas.decision import DecisionDraft
from src.services import event_bus
from src.services.email import EmailMessage, EmailProvider, get_email_provider
from src.services.email.render import render as render_email
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
        email_status=record.email_status if record is not None else None,
        approved_by=record.approved_by if record is not None else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


async def _load_task_with_decision(session: AsyncSession, task_id: str) -> Task:
    task = (
        await session.execute(
            select(Task).where(Task.task_id == task_id).options(selectinload(Task.decision))
        )
    ).scalar_one_or_none()
    if task is None:
        raise TaskNotFoundError(f"task {task_id} not found")
    return task


@router.patch("/{task_id}/decision", response_model=ApplicationStatusResponse)
async def modify_decision(
    task_id: str,
    body: ModifyDecisionRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ApplicationStatusResponse:
    task = await _load_task_with_decision(session, task_id)
    record = task.decision
    if record is None:
        raise InvalidStateTransitionError("no draft decision to modify yet")

    if body.verdict is not None:
        record.verdict = body.verdict
    if body.premium_loading_pct is not None:
        record.premium_loading_pct = body.premium_loading_pct
    if body.conditions is not None:
        record.conditions = json.dumps(body.conditions)
    if body.reasoning is not None:
        record.reasoning = body.reasoning
    task.status = TaskStatus.modified
    await session.commit()

    return await get_application(task_id, session)


@router.post("/{task_id}/approve", response_model=ApproveResponse)
async def approve_decision(
    task_id: str,
    body: ApproveRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    email: Annotated[EmailProvider, Depends(get_email_provider)],
) -> ApproveResponse:
    task = await _load_task_with_decision(session, task_id)
    record = task.decision
    if record is None:
        raise InvalidStateTransitionError("no decision to approve yet")
    if task.status not in {TaskStatus.awaiting_review, TaskStatus.modified}:
        raise InvalidStateTransitionError(f"cannot approve from status {task.status.value}")

    application = (
        await session.execute(select(Application).where(Application.id == task.application_id))
    ).scalar_one()
    profile = ApplicantProfile.model_validate_json(application.data)

    draft = DecisionDraft(
        verdict=record.verdict,  # type: ignore[arg-type]
        premium_loading_pct=record.premium_loading_pct,
        conditions=json.loads(record.conditions),
        reasoning=record.reasoning,
        citations=json.loads(record.citations),
    )

    to_addr = body.notify_email or profile.demographics.email
    subject, html, text = render_email(
        task.reference_number,
        f"{profile.demographics.first_name} {profile.demographics.last_name}",
        draft,
    )
    result = await email.send(EmailMessage(to=to_addr, subject=subject, html=html, text=text))

    record.approved_by = body.approved_by
    record.email_status = result.status
    record.provider_message_id = result.provider_message_id
    task.status = TaskStatus.sent if result.status == "sent" else TaskStatus.approved
    await session.commit()

    return ApproveResponse(
        status=task.status.value,
        email_status=result.status,
        provider_message_id=result.provider_message_id,
    )


@router.post("/{task_id}/reeval", response_model=ReevalResponse)
async def reevaluate(
    task_id: str,
    body: ReevalRequest,
    background: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReevalResponse:
    task = await _load_task_with_decision(session, task_id)
    if task.status in {TaskStatus.queued, TaskStatus.running}:
        raise InvalidStateTransitionError(
            "task is already running; wait for it to complete before re-evaluating"
        )

    application = (
        await session.execute(select(Application).where(Application.id == task.application_id))
    ).scalar_one()
    profile = ApplicantProfile.model_validate_json(application.data)

    if task.decision is not None:
        await session.delete(task.decision)
    task.status = TaskStatus.reeval
    await session.commit()

    upload_root = Path(settings.UPLOAD_DIR) / task_id
    paths = sorted(str(p) for p in upload_root.glob("*")) if upload_root.exists() else []
    if not paths:
        paths = list(profile.medical_docs)

    background.add_task(run_task, task_id, profile, paths)
    return ReevalResponse(task_id=task_id, status=task.status.value)


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
