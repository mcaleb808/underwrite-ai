from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class Demographics(BaseModel):
    first_name: str
    last_name: str
    dob: date
    sex: Literal["M", "F"]
    email: EmailStr
    phone_e164: str | None = None
    nid: str = Field(min_length=16, max_length=16)
    district: str
    province: str
    ubudehe_category: Literal[1, 2, 3, 4]
    cbhi_status: Literal["enrolled", "lapsed", "not_applicable"]


class Lifestyle(BaseModel):
    tobacco: Literal["none", "occasional", "daily"]
    alcohol_units_per_week: int = 0
    exercise_days_per_week: int = 0


class Vitals(BaseModel):
    height_cm: float
    weight_kg: float
    sbp: int | None = None
    dbp: int | None = None


class Occupation(BaseModel):
    title: str
    class_: Literal["I", "II", "III"] = Field(alias="class")

    model_config = {"populate_by_name": True}


class ApplicantProfile(BaseModel):
    applicant_id: str
    demographics: Demographics
    occupation: Occupation
    lifestyle: Lifestyle
    vitals: Vitals
    declared_history: list[str] = []
    sum_insured_rwf: int
    medical_docs: list[str] = []
