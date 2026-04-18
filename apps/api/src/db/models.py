import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TaskStatus(enum.StrEnum):
    queued = "queued"
    running = "running"
    awaiting_review = "awaiting_review"
    approved = "approved"
    modified = "modified"
    reeval = "reeval"
    sent = "sent"
    failed = "failed"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    applicant_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    data: Mapped[str] = mapped_column(Text)  # json-serialized ApplicantProfile
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    tasks: Mapped[list["Task"]] = relationship(back_populates="application")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    reference_number: Mapped[str] = mapped_column(String(20))
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.queued)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_band: Mapped[str | None] = mapped_column(String(16), nullable=True)
    risk_factors_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    application: Mapped["Application"] = relationship(back_populates="tasks")
    events: Mapped[list["Event"]] = relationship(back_populates="task")
    decision: Mapped["DecisionRecord | None"] = relationship(back_populates="task")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(32), ForeignKey("tasks.task_id"), index=True)
    node: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text)  # json
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["Task"] = relationship(back_populates="events")


class DecisionRecord(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(32), ForeignKey("tasks.task_id"), unique=True)
    verdict: Mapped[str] = mapped_column(String(32))
    premium_loading_pct: Mapped[float] = mapped_column(Float, default=0.0)
    conditions: Mapped[str] = mapped_column(Text, default="[]")  # json list
    reasoning: Mapped[str] = mapped_column(Text)
    citations: Mapped[str] = mapped_column(Text, default="[]")  # json list
    approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["Task"] = relationship(back_populates="decision")
