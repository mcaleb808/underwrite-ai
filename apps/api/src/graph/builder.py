"""Build and compile the underwriting graph."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.graph.nodes import critic, decision_draft, doc_parser, guidelines_rag, risk_assessor
from src.graph.routing import route_after_critic
from src.graph.state import UnderwritingState


def build_graph():
    g = StateGraph(UnderwritingState)

    g.add_node("doc_parser", doc_parser.run)
    g.add_node("risk_assessor", risk_assessor.run)
    g.add_node("guidelines_rag", guidelines_rag.run)
    g.add_node("decision_draft", decision_draft.run)
    g.add_node("critic", critic.run)

    g.add_edge(START, "doc_parser")
    # parallel fan-out after doc_parser
    g.add_edge("doc_parser", "risk_assessor")
    g.add_edge("doc_parser", "guidelines_rag")
    # join into decision_draft
    g.add_edge("risk_assessor", "decision_draft")
    g.add_edge("guidelines_rag", "decision_draft")
    g.add_edge("decision_draft", "critic")
    g.add_conditional_edges(
        "critic",
        route_after_critic,
        {"revise": "decision_draft", "finalize": END},
    )

    return g.compile(checkpointer=MemorySaver())
