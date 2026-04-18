"""District-level endemic prevalence lookup per UW-070."""

import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "districts.json"


class DistrictRow(TypedDict):
    name: str
    province: str
    malaria_per_1000: float
    tb_per_100k: float
    hiv_prevalence_pct: float
    htn_prevalence_pct: float
    dm_prevalence_pct: float


@lru_cache(maxsize=1)
def _load() -> dict[str, DistrictRow]:
    rows: list[DistrictRow] = json.loads(DATA_PATH.read_text())
    return {row["name"]: row for row in rows}


def lookup_district(name: str) -> DistrictRow | None:
    return _load().get(name)


def endemic_loading(name: str) -> float:
    """Return malaria-driven endemic loading capped at +10 per UW-070."""
    row = lookup_district(name)
    if row is None:
        return 0.0
    return min(10.0, row["malaria_per_1000"] / 5.0)
