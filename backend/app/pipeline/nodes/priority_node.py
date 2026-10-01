import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from app.pipeline.state import GapFinderState
from app.config import get_settings

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=get_settings().groq_api_key,
    temperature=0.1,
)


def priority_node(state: GapFinderState) -> dict:
    gaps = state.get("gaps", [])
    raw_text = state.get("raw_text", "")

    if not gaps:
        return {"prioritized_gaps": [], "status": "No gaps to prioritize"}

    gap_list = [g["concept"] for g in gaps]

    prompt = f"""You are ranking knowledge gaps in lecture notes by importance.

For each concept below, assign a severity:
- "high"   = foundational, other concepts depend on it, mentioned many times
- "medium" = important but more isolated
- "low"    = peripheral, mentioned once

Concepts to rank: {json.dumps(gap_list)}

Full lecture text for context:
{raw_text[:3000]}

Return ONLY a JSON object mapping concept -> severity.
Example: {{"attention mechanism": "high", "BLEU score": "low"}}
"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        severity_map = json.loads(content.strip())
    except Exception:
        severity_map = {g["concept"]: "medium" for g in gaps}

    order = {"high": 0, "medium": 1, "low": 2}
    ranked = []
    for gap in gaps:
        gap = dict(gap)
        gap["severity"] = severity_map.get(gap["concept"], gap.get("severity", "medium"))
        ranked.append(gap)

    ranked.sort(key=lambda g: order.get(g["severity"], 1))

    high_count = sum(1 for g in ranked if g["severity"] == "high")
    return {
        "prioritized_gaps": ranked,
        "status": f"Prioritized {len(ranked)} gaps",
        "messages": [AIMessage(content=f"Ranked gaps -- {high_count} high priority")],
    }
