"""Smoke test - run the stub graph end-to-end and print event trace."""

import uuid

from src.graph.builder import build_graph


def main():
    graph = build_graph()
    config = {"configurable": {"thread_id": uuid.uuid4().hex}}

    result = graph.invoke({"task_id": "smoke-test", "events": []}, config)

    events = result.get("events", [])
    print(f"\n{'=' * 50}")
    print(f"Smoke test complete - {len(events)} events captured")
    print(f"{'=' * 50}")
    for i, event in enumerate(events, 1):
        print(f"  {i}. [{event.get('node', '?')}] {event.get('type', '?')}")
    print()

    assert len(events) == 5, f"expected 5 events, got {len(events)}"
    expected_nodes = ["doc_parser", "risk_assessor", "guidelines_rag", "decision_draft", "critic"]
    actual_nodes = [e["node"] for e in events]
    for node in expected_nodes:
        assert node in actual_nodes, f"missing node: {node}"

    print("all assertions passed")


if __name__ == "__main__":
    main()
