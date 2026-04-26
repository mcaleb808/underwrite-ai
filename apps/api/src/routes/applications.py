"""Application intake and status routes."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import ValidationError
from sqlalchemy import delete, func, select
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
    ApplicationListItem,
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
from src.schemas.decision import DecisionDraft, RiskFactor
from src.schemas.events import OrchestratorClosed, OrchestratorError
from src.services import event_bus
from src.services.email import EmailMessage, EmailProvider, get_email_provider
from src.services.email.render import render as render_email
from src.services.orchestrator import request_cancel, run_task
from src.services.reference import new_reference

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


async def _save_uploads(task_id: str, files: list[UploadFile]) -> list[str]:
    target_dir = (Path(settings.UPLOAD_DIR) / task_id).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for upload in files:
        if not upload.filename:
            continue
        dest = target_dir / Path(upload.filename).name
        dest.write_bytes(await upload.read())
        saved.append(str(dest))
    return saved


def _copy_seed_docs(task_id: str, profile: ApplicantProfile) -> list[str]:
    """Persona runs ship their PDFs in src/data/. Copy them into the task's
    upload dir so the same files are downloadable from the dashboard and
    the doc_parser sees them at deterministic absolute paths."""
    target_dir = (Path(settings.UPLOAD_DIR) / task_id).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    out: list[str] = []
    for rel in profile.medical_docs:
        src = DATA_DIR / rel
        if not src.is_file():
            continue
        dest = target_dir / src.name
        dest.write_bytes(src.read_bytes())
        out.append(str(dest))
    return out


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
    if not paths and profile.medical_docs:
        paths = _copy_seed_docs(task_id, profile)

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


@router.get("", response_model=list[ApplicationListItem])
async def list_applications(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[ApplicationListItem]:
    rows = (
        await session.execute(
            select(Task, Application.applicant_id, DecisionRecord.verdict)
            .join(Application, Task.application_id == Application.id)
            .join(DecisionRecord, DecisionRecord.task_id == Task.task_id, isouter=True)
            .order_by(Task.created_at.desc())
            .limit(limit)
        )
    ).all()
    return [
        ApplicationListItem(
            task_id=task.task_id,
            reference_number=task.reference_number,
            status=task.status.value,
            risk_score=task.risk_score,
            risk_band=task.risk_band,
            verdict=verdict,
            applicant_id=applicant_id,
            created_at=task.created_at,
        )
        for task, applicant_id, verdict in rows
    ]


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

    risk_factors: list[RiskFactor] = []
    if task.risk_factors_json:
        try:
            risk_factors = [RiskFactor(**f) for f in json.loads(task.risk_factors_json)]
        except (ValueError, TypeError):
            risk_factors = []

    return ApplicationStatusResponse(
        task_id=task.task_id,
        reference_number=task.reference_number,
        status=task.status.value,
        risk_score=task.risk_score,
        risk_band=task.risk_band,
        risk_factors=risk_factors,
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


_TERMINAL_STATUSES = {
    TaskStatus.awaiting_review,
    TaskStatus.approved,
    TaskStatus.modified,
    TaskStatus.sent,
    TaskStatus.failed,
    TaskStatus.cancelled,
}


async def _delete_task_rows(session: AsyncSession, task_ids: list[str]) -> None:
    """Wipe events, decisions, task rows, and orphaned applications for the ids."""
    if not task_ids:
        return
    task_rows = (
        (await session.execute(select(Task).where(Task.task_id.in_(task_ids)))).scalars().all()
    )
    app_ids = {t.application_id for t in task_rows}
    await session.execute(delete(Event).where(Event.task_id.in_(task_ids)))
    await session.execute(delete(DecisionRecord).where(DecisionRecord.task_id.in_(task_ids)))
    await session.execute(delete(Task).where(Task.task_id.in_(task_ids)))
    for app_id in app_ids:
        remaining = (
            await session.execute(select(func.count(Task.id)).where(Task.application_id == app_id))
        ).scalar_one()
        if remaining == 0:
            await session.execute(delete(Application).where(Application.id == app_id))


@router.post("/{task_id}/cancel", status_code=202)
async def cancel_task(
    task_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    """Signal a running task to stop after its current node finishes."""
    task = (await session.execute(select(Task).where(Task.task_id == task_id))).scalar_one_or_none()
    if task is None:
        raise TaskNotFoundError(task_id)
    if task.status not in {TaskStatus.queued, TaskStatus.running, TaskStatus.reeval}:
        raise InvalidStateTransitionError(f"cannot cancel from status {task.status.value}")
    request_cancel(task_id)
    return {"status": "cancelling"}


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    """Hard-delete a task and its events / decision / orphaned application."""
    task = (await session.execute(select(Task).where(Task.task_id == task_id))).scalar_one_or_none()
    if task is None:
        raise TaskNotFoundError(task_id)
    if task.status in {TaskStatus.running, TaskStatus.queued, TaskStatus.reeval}:
        raise InvalidStateTransitionError(
            "cannot delete an in-flight task - cancel it first, then delete"
        )
    await _delete_task_rows(session, [task_id])
    await session.commit()
    return Response(status_code=204)


@router.delete("", status_code=204)
async def clear_terminal_tasks(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    """Hard-delete every task in a terminal state. In-flight tasks are skipped."""
    rows = (
        (await session.execute(select(Task).where(Task.status.in_(_TERMINAL_STATUSES))))
        .scalars()
        .all()
    )
    await _delete_task_rows(session, [t.task_id for t in rows])
    await session.commit()
    return Response(status_code=204)


@router.get("/{task_id}/files", response_model=list[str])
async def list_files(task_id: str) -> list[str]:
    """List filenames of medical PDFs uploaded for this task."""
    upload_dir = (Path(settings.UPLOAD_DIR) / task_id).resolve()
    if not upload_dir.exists():
        return []
    return sorted(p.name for p in upload_dir.iterdir() if p.is_file())


@router.get("/{task_id}/files/{filename}")
async def get_file(task_id: str, filename: str) -> FileResponse:
    """Stream a single uploaded medical document."""
    base = (Path(settings.UPLOAD_DIR) / task_id).resolve()
    target = (base / filename).resolve()
    # path traversal guard: target must be a child of base
    if base not in target.parents or not target.is_file():
        raise TaskNotFoundError(f"file {filename} not found for task {task_id}")
    media_type = (
        "application/pdf" if target.suffix.lower() == ".pdf" else "application/octet-stream"
    )
    return FileResponse(target, media_type=media_type, filename=target.name)


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
                yield _sse(OrchestratorError(error="task not found").model_dump())
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
                # Flatten the persisted payload so replayed events match the
                # live stream's shape (the timeline reads top-level fields).
                payload = json.loads(row.payload)
                event = {**payload, "node": row.node, "type": row.event_type}
                event["ts"] = row.timestamp.isoformat()
                yield _sse(event)

            # if the task already finished, no live events will arrive
            if existing_task.status in {
                TaskStatus.awaiting_review,
                TaskStatus.approved,
                TaskStatus.modified,
                TaskStatus.sent,
                TaskStatus.failed,
            }:
                yield _sse(OrchestratorClosed().model_dump())
                return

        async for event in event_bus.stream(task_id):
            yield _sse(event)
        yield _sse({"node": "orchestrator", "type": "closed"})

    return StreamingResponse(generator(), media_type="text/event-stream")
