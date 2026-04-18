"""Read-only access to seed applicant personas, used by the demo dashboard."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from src.exceptions import TaskNotFoundError
from src.schemas.applicant import ApplicantProfile

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "applicants"

router = APIRouter(prefix="/api/v1/personas", tags=["personas"])


class PersonaSummary(BaseModel):
    id: str
    name: str
    age: int
    district: str
    headline: str


def _summarize(profile: ApplicantProfile) -> PersonaSummary:
    today = date.today()
    age = (
        today.year
        - profile.demographics.dob.year
        - (
            (today.month, today.day)
            < (profile.demographics.dob.month, profile.demographics.dob.day)
        )
    )
    history = profile.declared_history or ["no declared history"]
    return PersonaSummary(
        id=profile.applicant_id,
        name=f"{profile.demographics.first_name} {profile.demographics.last_name}",
        age=age,
        district=profile.demographics.district,
        headline=", ".join(history),
    )


@router.get("", response_model=list[PersonaSummary])
async def list_personas() -> list[PersonaSummary]:
    out: list[PersonaSummary] = []
    for path in sorted(DATA_DIR.glob("*.json")):
        profile = ApplicantProfile.model_validate_json(path.read_text())
        out.append(_summarize(profile))
    return out


@router.get("/{persona_id}")
async def get_persona(persona_id: str) -> dict:
    path = DATA_DIR / f"{persona_id}.json"
    if not path.exists():
        raise TaskNotFoundError(f"persona {persona_id} not found")
    return json.loads(path.read_text())
