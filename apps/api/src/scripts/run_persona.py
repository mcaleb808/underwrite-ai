"""Run doc_parser + risk_assessor on a single persona for manual verification.

Usage:
    uv run python -m src.scripts.run_persona alice-kigali-clean
    uv run python -m src.scripts.run_persona jean-nyanza-controlled-htn

Calls the real LLM via OpenRouter for PDF parsing — costs ~$0.001/run.
"""

import json
import sys
from pathlib import Path

from src.graph.nodes import doc_parser, risk_assessor
from src.schemas.applicant import ApplicantProfile

APPLICANTS_DIR = Path(__file__).resolve().parent.parent / "data" / "applicants"


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python -m src.scripts.run_persona <applicant_id>", file=sys.stderr)
        sys.exit(2)

    applicant_id = sys.argv[1]
    profile = ApplicantProfile.model_validate_json(
        (APPLICANTS_DIR / f"{applicant_id}.json").read_text()
    )

    state: dict = {"task_id": f"manual-{applicant_id}", "applicant": profile, "events": []}

    print(f"\n=== {applicant_id} ===")
    print(f"parsing {len(profile.medical_docs)} medical doc(s)...")
    parsed_update = doc_parser.run(state)
    state.update(parsed_update)
    parsed = state["parsed_medical"]
    print(f"  parsed {len(parsed)} record(s)")
    for record in parsed:
        print(f"    - {Path(record.source_path).name}")
        print(f"      diagnoses: {[d.code for d in record.diagnoses]}")
        print(f"      labs: {[(lab.name, lab.value, lab.flag) for lab in record.labs]}")

    print("\nassessing risk...")
    risk_update = risk_assessor.run(state)
    state.update(risk_update)

    print(f"\nrisk_score: {state['risk_score']}")
    print(f"risk_band:  {state['risk_band']}")
    print("risk_factors:")
    for f in state["risk_factors"]:
        print(f"  - {f.name:30s} +{f.contribution:>5.1f}  ({f.evidence})")

    print("\nevents:")
    print(json.dumps(state["events"], indent=2, default=str))


if __name__ == "__main__":
    main()
