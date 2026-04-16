from typing import Literal

from pydantic import BaseModel


class Lab(BaseModel):
    name: str
    value: str
    unit: str | None = None
    reference_range: str | None = None
    flag: Literal["high", "low", "normal"] | None = None


class Vital(BaseModel):
    name: str
    value: str
    unit: str | None = None


class Diagnosis(BaseModel):
    code: str  # short label, e.g. "hypertension", "T2DM"
    description: str
    status: Literal["active", "controlled", "resolved"] | None = None


class Medication(BaseModel):
    name: str
    dosage: str | None = None
    frequency: str | None = None


class ParsedMedicalRecord(BaseModel):
    source_path: str
    patient_block: str | None = None
    vitals: list[Vital] = []
    labs: list[Lab] = []
    diagnoses: list[Diagnosis] = []
    medications: list[Medication] = []
    notes_excerpts: list[str] = []
