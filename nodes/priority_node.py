"""
PriorityNode — Step 3
Ranks detected gaps by severity:
  HIGH   — blocks understanding of multiple other concepts
  MEDIUM — mentioned frequently but unexplained
  LOW    — mentioned once in passing
"""
import os
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from state import GapFinderState, Gap

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1
)


def priority_node(state: GapFinderState) -> dict:
    """LangGraph node: rank gaps by importance."""
    gaps = state.get("gaps", [])
    raw_text = state.get("raw_text", "")

    if not gaps:
        return {"prioritized_gaps": [], "status": "⚠️ No gaps to prioritize"}

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

    # Apply severity scores, then sort: high > medium > low
    order = {"high": 0, "medium": 1, "low": 2}
    ranked = []
    for gap in gaps:
        gap = dict(gap)
        gap["severity"] = severity_map.get(gap["concept"], gap.get("severity", "medium"))
        ranked.append(gap)

    ranked.sort(key=lambda g: order.get(g["severity"], 1))

    return {
        "prioritized_gaps": ranked,
        "status": f"📊 Prioritized {len(ranked)} gaps",
        "messages": [AIMessage(content=f"Ranked gaps — {sum(1 for g in ranked if g['severity']=='high')} high priority")]
    }
