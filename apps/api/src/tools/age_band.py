"""Age computation and band lookup per UW-010."""

from datetime import date
from typing import Literal

AgeBand = Literal["18_30", "31_45", "46_55", "56_65", "66_70", "out_of_range"]


def compute_age(dob: date, on: date | None = None) -> int:
    today = on or date.today()
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return years


def classify_age_band(age: int) -> AgeBand:
    if 18 <= age <= 30:
        return "18_30"
    if 31 <= age <= 45:
        return "31_45"
    if 46 <= age <= 55:
        return "46_55"
    if 56 <= age <= 65:
        return "56_65"
    if 66 <= age <= 70:
        return "66_70"
    return "out_of_range"
