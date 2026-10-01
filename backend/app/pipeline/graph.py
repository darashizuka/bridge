import logging
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage
from app.pipeline.state import GapFinderState
from app.pipeline.nodes.parse_node import parse_node
from app.pipeline.nodes.gap_detect_node import gap_detect_node
from app.pipeline.nodes.priority_node import priority_node
from app.pipeline.nodes.fill_node import fill_node
from app.pipeline.nodes.connect_node import connect_node
from app.pipeline.nodes.output_node import output_node

logger = logging.getLogger(__name__)


def safe_node(node_fn, node_name: str):
    def wrapper(state: GapFinderState) -> dict:
        try:
            return node_fn(state)
        except Exception as e:
            logger.exception(f"Node {node_name} failed: {e}")
            return {
                "status": f"Error in {node_name}: {str(e)}",
                "messages": [AIMessage(content=f"Warning: {node_name} failed: {str(e)}")],
            }
    wrapper.__name__ = node_name
    return wrapper


def build_graph():
    graph = StateGraph(GapFinderState)

    graph.add_node("parse", safe_node(parse_node, "parse"))
    graph.add_node("gap_detect", safe_node(gap_detect_node, "gap_detect"))
    graph.add_node("prioritize", safe_node(priority_node, "prioritize"))
    graph.add_node("fill", safe_node(fill_node, "fill"))
    graph.add_node("connect", safe_node(connect_node, "connect"))
    graph.add_node("output", safe_node(output_node, "output"))

    graph.set_entry_point("parse")
    graph.add_edge("parse", "gap_detect")
    graph.add_edge("gap_detect", "prioritize")
    graph.add_edge("prioritize", "fill")
    graph.add_edge("fill", "connect")
    graph.add_edge("connect", "output")
    graph.add_edge("output", END)

    return graph.compile()
