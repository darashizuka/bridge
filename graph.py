"""
LangGraph Graph Definition
Wires all nodes into a sequential pipeline:
parse → gap_detect → prioritize → fill → connect → output
"""
from langgraph.graph import StateGraph, END
from state import GapFinderState
from nodes.parse_node import parse_node
from nodes.gap_detect_node import gap_detect_node
from nodes.priority_node import priority_node
from nodes.fill_node import fill_node
from nodes.connect_node import connect_node
from nodes.output_node import output_node


def build_graph():
    """Build and compile the LangGraph pipeline."""
    graph = StateGraph(GapFinderState)

    # Register all nodes
    graph.add_node("parse",      parse_node)
    graph.add_node("gap_detect", gap_detect_node)
    graph.add_node("prioritize", priority_node)
    graph.add_node("fill",       fill_node)
    graph.add_node("connect",    connect_node)
    graph.add_node("output",     output_node)

    # Wire sequentially
    graph.set_entry_point("parse")
    graph.add_edge("parse",      "gap_detect")
    graph.add_edge("gap_detect", "prioritize")
    graph.add_edge("prioritize", "fill")
    graph.add_edge("fill",       "connect")
    graph.add_edge("connect",    "output")
    graph.add_edge("output",     END)

    return graph.compile()


# Singleton compiled graph
app = build_graph()
