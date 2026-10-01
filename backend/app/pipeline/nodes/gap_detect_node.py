import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from app.pipeline.state import GapFinderState, Gap
from app.pipeline.tools.vectorstore import is_concept_explained
from app.config import get_settings

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=get_settings().groq_api_key,
    temperature=0.1,
)


def gap_detect_node(state: GapFinderState) -> dict:
    concepts = state.get("all_concepts", [])
    raw_text = state.get("raw_text", "")
    analysis_id = state.get("analysis_id", "default")

    if not concepts:
        return {"gaps": [], "status": "No concepts to analyze"}

    gaps = []
    for concept in concepts:
        is_explained, _ = is_concept_explained(concept, analysis_id)
        if not is_explained:
            context = _find_context(concept, raw_text)
            gaps.append(Gap(
                concept=concept,
                context=context,
                severity="medium",
                explanation="",
                flashcard_q="",
                flashcard_a="",
                sources=[],
            ))

    assumed = _detect_assumed_knowledge(raw_text)
    for concept in assumed:
        if concept not in [g["concept"] for g in gaps]:
            gaps.append(Gap(
                concept=concept,
                context="Assumed prerequisite -- never introduced in these notes",
                severity="high",
                explanation="",
                flashcard_q="",
                flashcard_a="",
                sources=[],
            ))

    return {
        "gaps": gaps,
        "status": f"Found {len(gaps)} knowledge gaps",
        "messages": [AIMessage(content=f"Detected {len(gaps)} gaps out of {len(concepts)} concepts")],
    }


def _find_context(concept: str, text: str) -> str:
    sentences = text.replace("\n", " ").split(".")
    concept_lower = concept.lower()
    for sentence in sentences:
        if concept_lower in sentence.lower():
            return sentence.strip()[:200]
    return f'Appears in the notes as "{concept}"'


def _detect_assumed_knowledge(raw_text: str) -> list[str]:
    prompt = f"""You are analyzing lecture notes.

Find concepts that are assumed known but never actually defined or explained in these notes.
Look for phrases like: "as you know", "recall that", "assuming you're familiar with",
"using X" without explaining X, referencing a term once without definition.

Return ONLY a JSON array of concept strings. Max 5 items. No duplicates.
If nothing found, return [].

LECTURE TEXT:
{raw_text[:3000]}
"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())
    except Exception:
        return []
