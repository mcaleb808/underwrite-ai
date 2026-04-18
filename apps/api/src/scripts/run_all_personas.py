"""Run the full graph on every seed persona and print a verdict summary table."""

import uuid
from pathlib import Path

from src.graph.builder import build_graph
from src.schemas.applicant import ApplicantProfile

APPLICANTS_DIR = Path(__file__).resolve().parent.parent / "data" / "applicants"


def main() -> None:
    graph = build_graph()
    rows: list[tuple[str, float, str, str, float, int, bool]] = []
    for f in sorted(APPLICANTS_DIR.glob("*.json")):
        profile = ApplicantProfile.model_validate_json(f.read_text())
        config = {"configurable": {"thread_id": uuid.uuid4().hex}}
        state = graph.invoke(
            {"task_id": f"demo-{f.stem}", "applicant": profile, "events": []},
            config,
        )
        decision = state["decision"]
        critique = state.get("critique")
        rows.append(
            (
                f.stem,
                state["risk_score"],
                state["risk_band"],
                decision.verdict,
                decision.premium_loading_pct,
                state.get("revision_count", 0),
                bool(critique and critique.bias_flag),
            )
        )

    print()
    header = (
        f"{'persona':32s} {'score':>6s} {'band':12s} {'verdict':24s}"
        f" {'load%':>6s} {'rev':>3s} {'bias':>5s}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(f"{r[0]:32s} {r[1]:>6.1f} {r[2]:12s} {r[3]:24s} {r[4]:>6.1f} {r[5]:>3d} {r[6]!s:>5s}")
    print()


if __name__ == "__main__":
    main()
