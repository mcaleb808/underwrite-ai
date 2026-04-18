"""Run the full underwriting graph on a single persona.

Usage:
    uv run python -m src.scripts.run_persona alice-kigali-clean

Calls real LLMs via OpenRouter — costs ~$0.01/run with revisions.
"""

import json
import sys
import uuid
from pathlib import Path

from src.graph.builder import build_graph
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

    graph = build_graph()
    config = {"configurable": {"thread_id": uuid.uuid4().hex}}
    state = graph.invoke(
        {
            "task_id": f"manual-{applicant_id}",
            "applicant": profile,
            "events": [],
        },
        config,
    )

    print(f"\n=== {applicant_id} ===")
    print(f"risk_score: {state['risk_score']} ({state['risk_band']})")
    print("risk_factors:")
    for f in state["risk_factors"]:
        print(f"  - {f.name:30s} +{f.contribution:>5.1f}  ({f.evidence})")

    print(f"\nretrieved {len(state.get('retrieved_guidelines') or [])} guideline chunks")

    decision = state["decision"]
    print(f"\nverdict: {decision.verdict}")
    print(f"premium_loading_pct: {decision.premium_loading_pct}")
    print(f"conditions: {decision.conditions}")
    print(f"citations: {decision.citations}")
    print(f"\nreasoning:\n{decision.reasoning}")

    critique = state.get("critique")
    if critique is not None:
        print(f"\ncritic: needs_revision={critique.needs_revision} bias_flag={critique.bias_flag}")
        print(f"  issues: {critique.issues}")
        print(f"  suggestions: {critique.suggestions}")

    print(f"\nrevision_count: {state.get('revision_count', 0)}")
    print(f"\nevents ({len(state['events'])}):")
    print(json.dumps(state["events"], indent=2, default=str))


if __name__ == "__main__":
    main()
