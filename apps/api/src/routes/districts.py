"""Read-only access to the Rwandan districts list, used by the application form."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "districts.json"

router = APIRouter(prefix="/api/v1/districts", tags=["districts"])


class District(BaseModel):
    name: str
    province: str


@router.get("", response_model=list[District])
async def list_districts() -> list[District]:
    rows = json.loads(DATA_PATH.read_text())
    return [District(name=row["name"], province=row["province"]) for row in rows]
