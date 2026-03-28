"""
OutputNode — Step 6
Assembles the final study guide in Markdown format
and generates all flashcards as structured data.
"""
from langchain_core.messages import AIMessage
from state import GapFinderState


SEVERITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}


def output_node(state: GapFinderState) -> dict:
    """LangGraph node: generate final study guide and flashcards."""
    filled_gaps = state.get("filled_gaps", [])
    concept_dependencies = state.get("concept_dependencies", {})
    file_name = state.get("file_name", "your notes")

    if not filled_gaps:
        return {
            "study_guide": "# No gaps found! Your notes seem complete. 🎉",
            "flashcards": [],
            "status": "✅ Complete"
        }

    # Build study guide markdown
    lines = [
        f"# 📚 Lecture Gap Analysis — {file_name}",
        "",
        f"**{len(filled_gaps)} knowledge gaps found and filled.**",
        "",
        "---",
        "",
        "## 📖 Recommended Study Order",
        "",
        _build_study_order(filled_gaps, concept_dependencies),
        "",
        "---",
        "",
        "## 🔍 Gaps Explained",
        ""
    ]

    for gap in filled_gaps:
        concept = gap["concept"]
        severity = gap.get("severity", "medium")
        emoji = SEVERITY_EMOJI.get(severity, "🟡")
        deps = concept_dependencies.get(concept, [])

        lines.append(f"### {emoji} {concept.title()}")
        lines.append(f"*Priority: {severity.upper()}*")
        lines.append("")

        if gap.get("context") and "Assumed prerequisite" not in gap["context"]:
            lines.append(f"> **Appears in your notes as:** *\"{gap['context'][:150]}...\"*")
            lines.append("")

        if deps:
            lines.append(f"⚠️ **Study first:** {', '.join(deps)}")
            lines.append("")

        lines.append("**Explanation:**")
        lines.append(gap.get("explanation", "No explanation found."))
        lines.append("")

        if gap.get("sources"):
            lines.append("**Sources:**")
            for src in gap["sources"]:
                lines.append(f"- {src}")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines.append("## 🃏 Flashcards")
    lines.append("")
    lines.append("*Use these to test yourself!*")
    lines.append("")

    for i, gap in enumerate(filled_gaps, 1):
        if gap.get("flashcard_q"):
            lines.append(f"**Card {i}:** {gap['flashcard_q']}")
            lines.append(f"> {gap.get('flashcard_a', '')}")
            lines.append("")

    study_guide = "\n".join(lines)

    # Build flashcards as structured list
    flashcards = [
        {
            "concept": gap["concept"],
            "question": gap.get("flashcard_q", ""),
            "answer": gap.get("flashcard_a", ""),
            "severity": gap.get("severity", "medium")
        }
        for gap in filled_gaps
        if gap.get("flashcard_q")
    ]

    return {
        "study_guide": study_guide,
        "flashcards": flashcards,
        "status": "✅ Study guide ready!",
        "messages": [AIMessage(content=f"Generated study guide with {len(filled_gaps)} filled gaps and {len(flashcards)} flashcards")]
    }


def _build_study_order(gaps: list, deps: dict) -> str:
    """Topological sort for study order."""
    concepts = [g["concept"] for g in gaps]
    visited = set()
    order = []

    def visit(c):
        if c in visited or c not in concepts:
            return
        visited.add(c)
        for dep in deps.get(c, []):
            visit(dep)
        order.append(c)

    for c in concepts:
        visit(c)

    lines = []
    for i, concept in enumerate(order, 1):
        gap = next((g for g in gaps if g["concept"] == concept), None)
        severity = gap.get("severity", "medium") if gap else "medium"
        emoji = SEVERITY_EMOJI.get(severity, "🟡")
        lines.append(f"{i}. {emoji} **{concept.title()}**")

    return "\n".join(lines)
