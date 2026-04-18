"""BMI calculation and classification per UW-020."""

from typing import Literal

BmiClass = Literal["underweight", "normal", "overweight", "obese_1", "obese_2", "obese_3"]


def compute_bmi(height_cm: float, weight_kg: float) -> float:
    height_m = height_cm / 100
    return round(weight_kg / (height_m * height_m), 2)


def classify_bmi(bmi: float) -> BmiClass:
    if bmi < 18.5:
        return "underweight"
    if bmi < 25:
        return "normal"
    if bmi < 30:
        return "overweight"
    if bmi < 35:
        return "obese_1"
    if bmi < 40:
        return "obese_2"
    return "obese_3"
