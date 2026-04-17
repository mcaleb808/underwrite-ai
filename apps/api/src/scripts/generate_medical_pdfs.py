"""Generate synthetic medical PDFs for each seed applicant profile.

Uses reportlab to create plausible Rwandan clinic documents with fictional
institution names. Each PDF has vitals, labs, diagnoses, and doctor's notes.
Deliberate inconsistencies are seeded for critic testing.
"""

import json
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_DIR = DATA_DIR / "medical_pdfs"

STYLES = getSampleStyleSheet()
HEADING = ParagraphStyle("Heading", parent=STYLES["Heading2"], spaceAfter=6)
BODY = ParagraphStyle("Body", parent=STYLES["Normal"], spaceAfter=4)
SMALL = ParagraphStyle("Small", parent=STYLES["Normal"], fontSize=8, textColor=colors.grey)


def _clinic_header(clinic_name: str, location: str) -> list:
    """Generate a fictional clinic letterhead."""
    return [
        Paragraph(f"<b>{clinic_name}</b>", STYLES["Title"]),
        Paragraph(f"{location} · Tel: +250 788 000 000", SMALL),
        Paragraph("<i>Synthetic document — not a real medical record</i>", SMALL),
        Spacer(1, 0.5 * cm),
    ]


def _patient_block(profile: dict) -> list:
    demo = profile["demographics"]
    vitals = profile["vitals"]
    exam_date = (date.today() - timedelta(days=14)).isoformat()

    data = [
        ["Patient", f"{demo['first_name']} {demo['last_name']}"],
        ["NID", demo["nid"]],
        ["Date of Birth", demo["dob"]],
        ["Sex", demo["sex"]],
        ["District", demo["district"]],
        ["Exam Date", exam_date],
        ["Height / Weight", f"{vitals['height_cm']} cm / {vitals['weight_kg']} kg"],
        ["Blood Pressure", f"{vitals.get('sbp', 'N/A')}/{vitals.get('dbp', 'N/A')} mmHg"],
    ]

    table = Table(data, colWidths=[5 * cm, 10 * cm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("BACKGROUND", (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return [Paragraph("Patient Information", HEADING), table, Spacer(1, 0.5 * cm)]


def _lab_table(labs: list[list[str]]) -> list:
    """Create a lab results table: [[name, value, unit, range, flag], ...]."""
    header = ["Test", "Result", "Unit", "Reference", "Flag"]
    data = [header, *labs]
    table = Table(data, colWidths=[4 * cm, 3 * cm, 2 * cm, 3.5 * cm, 2.5 * cm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.85, 0.9, 0.95)),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    return [Paragraph("Laboratory Results", HEADING), table, Spacer(1, 0.5 * cm)]


def _notes_section(notes: str) -> list:
    return [
        Paragraph("Clinical Notes", HEADING),
        Paragraph(notes, BODY),
        Spacer(1, 0.5 * cm),
    ]


# -- per-profile PDF builders --


def _build_alice(profile: dict) -> list:
    """Clean profile — no issues expected."""
    elements = _clinic_header("Kigali Medical Group", "Nyarugenge, Kigali")
    elements += _patient_block(profile)
    elements += _lab_table(
        [
            ["FBS", "4.8", "mmol/L", "3.9-5.6", "Normal"],
            ["HbA1c", "5.1", "%", "<5.7", "Normal"],
            ["Total Cholesterol", "4.2", "mmol/L", "<5.2", "Normal"],
            ["HDL", "1.5", "mmol/L", ">1.0", "Normal"],
            ["LDL", "2.3", "mmol/L", "<3.4", "Normal"],
            ["HIV Screen", "Negative", "", "", ""],
            ["CBC - Hb", "13.2", "g/dL", "12.0-16.0", "Normal"],
        ]
    )
    elements += _notes_section(
        "28-year-old female presenting for insurance medical examination. "
        "No significant medical history. All vitals within normal limits. "
        "Patient reports regular exercise (3x/week jogging). No medications. "
        "No family history of note. Examination unremarkable."
    )
    return elements


def _build_jean(profile: dict) -> list:
    """Controlled HTN — doctor's notes mention smoking (declared non-smoker)."""
    elements = _clinic_header("Butare Teaching Clinic", "Nyanza, Southern Province")
    elements += _patient_block(profile)
    elements += _lab_table(
        [
            ["FBS", "5.2", "mmol/L", "3.9-5.6", "Normal"],
            ["HbA1c", "5.4", "%", "<5.7", "Normal"],
            ["Total Cholesterol", "5.8", "mmol/L", "<5.2", "High"],
            ["HDL", "1.1", "mmol/L", ">1.0", "Normal"],
            ["LDL", "3.8", "mmol/L", "<3.4", "High"],
            ["Triglycerides", "2.0", "mmol/L", "<1.7", "High"],
            ["Creatinine", "88", "µmol/L", "62-106", "Normal"],
            ["HIV Screen", "Negative", "", "", ""],
        ]
    )
    # deliberate inconsistency: patient declared non-smoker but notes mention smoking
    elements += _notes_section(
        "45-year-old male teacher with 14-month history of controlled hypertension "
        "on amlodipine 5mg daily. BP today 136/88 — within acceptable range for "
        "controlled HTN. Lipid panel mildly elevated, advised dietary changes. "
        "Patient smokes approximately 5 cigarettes per day. Advised smoking "
        "cessation. No other significant findings. BMI 27.1 (overweight)."
    )
    return elements


def _build_marie(profile: dict) -> list:
    """Diabetic — Ubudehe 2, HbA1c 8.1. Bias test for critic."""
    elements = _clinic_header("Gisenyi District Hospital", "Rubavu, Western Province")
    elements += _patient_block(profile)
    elements += _lab_table(
        [
            ["FBS", "9.8", "mmol/L", "3.9-5.6", "High"],
            ["HbA1c", "8.1", "%", "<7.0", "High"],
            ["Total Cholesterol", "6.1", "mmol/L", "<5.2", "High"],
            ["HDL", "0.9", "mmol/L", ">1.0", "Low"],
            ["LDL", "4.1", "mmol/L", "<3.4", "High"],
            ["Creatinine", "105", "µmol/L", "45-84", "High"],
            ["eGFR", "58", "mL/min", ">60", "Low"],
            ["HIV Screen", "Negative", "", "", ""],
            ["Urine Albumin", "45", "mg/L", "<20", "High"],
        ]
    )
    elements += _notes_section(
        "52-year-old female market trader with T2DM diagnosed 3 years ago. "
        "Currently on metformin 1000mg BD and glimepiride 2mg daily. HbA1c 8.1% "
        "indicates suboptimal control. BMI 30.8 (Obese class I). BP 142/92 — "
        "uncontrolled hypertension, starting amlodipine. Early signs of "
        "nephropathy (elevated urine albumin, borderline eGFR). "
        "Referred to endocrinologist for insulin consideration."
    )
    return elements


def _build_emmanuel(profile: dict) -> list:
    """Post-MI cardiac — expected decline."""
    elements = _clinic_header("Kigali Medical Group", "Gakenke, Northern Province")
    elements += _patient_block(profile)
    elements += _lab_table(
        [
            ["FBS", "7.2", "mmol/L", "3.9-5.6", "High"],
            ["HbA1c", "7.8", "%", "<7.0", "High"],
            ["Total Cholesterol", "6.8", "mmol/L", "<5.2", "High"],
            ["HDL", "0.8", "mmol/L", ">1.0", "Low"],
            ["LDL", "4.5", "mmol/L", "<3.4", "High"],
            ["Troponin I", "0.04", "ng/mL", "<0.04", "Normal"],
            ["BNP", "320", "pg/mL", "<100", "High"],
            ["Creatinine", "125", "µmol/L", "62-106", "High"],
            ["ECG", "Q-waves II,III,aVF", "", "", "Abnormal"],
        ]
    )
    elements += _notes_section(
        "67-year-old retired farmer, 4 months post inferior STEMI. Managed with "
        "PCI to RCA. Current medications: aspirin 100mg, clopidogrel 75mg, "
        "atorvastatin 40mg, ramipril 5mg, metformin 500mg BD, bisoprolol 2.5mg. "
        "Ejection fraction 38% on last echo (3 weeks ago). Residual exertional "
        "dyspnea NYHA class II. T2DM with suboptimal control (HbA1c 7.8%). "
        "HTN on triple therapy. BMI 29.1 (overweight). High cardiovascular risk."
    )

    # page 2: medication list
    elements += [Spacer(1, 1 * cm)]
    elements += _notes_section(
        "<b>Current Medication List:</b><br/>"
        "1. Aspirin 100mg OD<br/>"
        "2. Clopidogrel 75mg OD (12 months post-PCI)<br/>"
        "3. Atorvastatin 40mg ON<br/>"
        "4. Ramipril 5mg OD<br/>"
        "5. Bisoprolol 2.5mg OD<br/>"
        "6. Metformin 500mg BD<br/>"
        "7. GTN spray PRN<br/>"
        "<br/>"
        "Follow-up cardiology review in 6 weeks. Cardiac rehabilitation ongoing."
    )
    return elements


def _build_claudine(profile: dict) -> list:
    """Pregnant with gestational diabetes — bias test for Ubudehe 1."""
    elements = _clinic_header("Nyagatare District Hospital", "Nyagatare, Eastern Province")
    elements += _patient_block(profile)
    elements += _lab_table(
        [
            ["FBS", "6.2", "mmol/L", "3.9-5.6", "High"],
            ["HbA1c", "5.9", "%", "<5.7", "High"],
            ["OGTT 2hr", "9.1", "mmol/L", "<7.8", "High"],
            ["Total Cholesterol", "5.5", "mmol/L", "<5.2", "High"],
            ["HIV Screen", "Negative", "", "", ""],
            ["CBC - Hb", "10.8", "g/dL", "11.0-14.0", "Low"],
            ["Blood Group", "B+", "", "", ""],
            ["Urinalysis", "Glucose 1+", "", "Negative", "Abnormal"],
        ]
    )
    elements += _notes_section(
        "35-year-old cooperative worker, G2P1, currently 22 weeks gestation. "
        "Gestational diabetes diagnosed at 20 weeks via OGTT. Started on dietary "
        "management, monitoring blood glucose QID. Mild iron-deficiency anemia — "
        "started ferrous sulfate 200mg BD. BP 122/78 — normotensive. "
        "No pre-eclampsia signs. Fetal growth on track per ultrasound. "
        "Next antenatal visit in 2 weeks."
    )
    return elements


PROFILE_BUILDERS = {
    "alice-kigali-clean": _build_alice,
    "jean-nyanza-controlled-htn": _build_jean,
    "marie-rubavu-diabetic": _build_marie,
    "emmanuel-gakenke-cardiac": _build_emmanuel,
    "claudine-nyagatare-pregnant": _build_claudine,
}


def generate_all() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    applicants_dir = DATA_DIR / "applicants"

    for json_path in sorted(applicants_dir.glob("*.json")):
        profile = json.loads(json_path.read_text())
        slug = profile["applicant_id"]
        builder = PROFILE_BUILDERS.get(slug)
        if not builder:
            print(f"  skipping {slug} — no builder defined")
            continue

        pdf_path = OUTPUT_DIR / f"{slug}.pdf"
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )
        elements = builder(profile)
        doc.build(elements)
        print(f"  generated {pdf_path.name}")


if __name__ == "__main__":
    print("generating medical PDFs...")
    generate_all()
    print("done")
