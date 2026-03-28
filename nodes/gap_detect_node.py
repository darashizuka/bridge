"""
GapDetectNode — Step 2
For each concept extracted from the notes, checks ChromaDB
to see if the notes actually *explain* it or just mention it.
Concepts that are mentioned but not explained = GAPS.
"""
import os
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from state import GapFinderState, Gap
from tools.vectorstore import is_concept_explained

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1
)


def gap_detect_node(state: GapFinderState) -> dict:
    """LangGraph node: detect which concepts have no explanation in notes."""
    concepts = state.get("all_concepts", [])
    raw_text = state.get("raw_text", "")

    if not concepts:
        return {"gaps": [], "status": "⚠️ No concepts to analyze"}

    gaps = []

    # For each concept, use ChromaDB to check if it's explained
    for concept in concepts:
        is_explained, snippet = is_concept_explained(concept)

        if not is_explained:
            # Find the sentence where this concept appears for context
            context = _find_context(concept, raw_text)

            gaps.append(Gap(
                concept=concept,
                context=context,
                severity="medium",   # Will be set properly in priority_node
                explanation="",      # Will be filled by fill_node
                flashcard_q="",
                flashcard_a="",
                sources=[]
            ))

    # Use LLM to also detect "hand-wavy" sections and assumed prerequisites
    assumed = _detect_assumed_knowledge(raw_text)
    for concept in assumed:
        if concept not in [g["concept"] for g in gaps]:
            gaps.append(Gap(
                concept=concept,
                context="[Assumed prerequisite — never introduced in these notes]",
                severity="high",
                explanation="",
                flashcard_q="",
                flashcard_a="",
                sources=[]
            ))

    return {
        "gaps": gaps,
        "status": f"🔍 Found {len(gaps)} knowledge gaps",
        "messages": [AIMessage(content=f"Detected {len(gaps)} gaps out of {len(concepts)} concepts")]
    }


def _find_context(concept: str, text: str) -> str:
    """Find the sentence containing the concept for context."""
    sentences = text.replace("\n", " ").split(".")
    concept_lower = concept.lower()
    for sentence in sentences:
        if concept_lower in sentence.lower():
            return sentence.strip()[:200]
    return f'Appears in the notes as "{concept}"'


def _detect_assumed_knowledge(raw_text: str) -> list[str]:
    """Use LLM to find concepts that are assumed but never introduced."""
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
