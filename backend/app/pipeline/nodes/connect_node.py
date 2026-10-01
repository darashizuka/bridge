import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from app.pipeline.state import GapFinderState
from app.config import get_settings

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=get_settings().groq_api_key,
    temperature=0.2,
)


def connect_node(state: GapFinderState) -> dict:
    filled_gaps = state.get("filled_gaps", [])
    all_concepts = state.get("all_concepts", [])

    if not filled_gaps:
        return {"concept_dependencies": {}, "status": "No concepts to connect"}

    gap_concepts = [g["concept"] for g in filled_gaps]

    prompt = f"""You are mapping concept dependencies for a student's study guide.

Given these knowledge gaps (concepts the student needs to learn):
{json.dumps(gap_concepts)}

And the full list of concepts from their notes:
{json.dumps(all_concepts[:30])}

For each gap concept, list which OTHER concepts from the gap list it depends on
(i.e., you need to understand X before understanding this concept).
Only include dependencies that are in the gap list.
If no dependencies, use an empty array.

Return ONLY a JSON object like:
{{
  "multi-head attention": ["attention mechanism", "linear algebra"],
  "transformer": ["multi-head attention", "positional encoding"],
  "softmax": []
}}
"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        deps = json.loads(content.strip())
    except Exception:
        deps = {g["concept"]: [] for g in filled_gaps}

    return {
        "concept_dependencies": deps,
        "status": f"Mapped dependencies for {len(deps)} concepts",
        "messages": [AIMessage(content="Built concept dependency map")],
    }
