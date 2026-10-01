from langchain_core.messages import AIMessage
from app.pipeline.state import GapFinderState

SEVERITY_LABEL = {"high": "High", "medium": "Medium", "low": "Low"}


def output_node(state: GapFinderState) -> dict:
    filled_gaps = state.get("filled_gaps", [])
    concept_dependencies = state.get("concept_dependencies", {})
    file_name = state.get("file_name", "your notes")

    if not filled_gaps:
        return {
            "study_guide": "# No gaps found\n\nYour notes appear to be complete.",
            "flashcards": [],
            "status": "Complete",
        }

    lines = [
        f"# Gap Analysis: {file_name}",
        "",
        f"**{len(filled_gaps)} knowledge gaps found and filled.**",
        "",
        "---",
        "",
        "## Recommended Study Order",
        "",
        _build_study_order(filled_gaps, concept_dependencies),
        "",
        "---",
        "",
        "## Gaps Explained",
        "",
    ]

    for gap in filled_gaps:
        concept = gap["concept"]
        severity = gap.get("severity", "medium")
        label = SEVERITY_LABEL.get(severity, "Medium")
        deps = concept_dependencies.get(concept, [])

        lines.append(f"### {concept.title()}")
        lines.append(f"*Priority: {label}*")
        lines.append("")

        ctx = gap.get("context", "")
        if ctx and "Assumed prerequisite" not in ctx:
            lines.append(f"> Appears in your notes as: *\"{ctx[:150]}...\"*")
            lines.append("")

        if deps:
            lines.append(f"**Study first:** {', '.join(deps)}")
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

    study_guide = "\n".join(lines)

    flashcards = [
        {
            "concept": gap["concept"],
            "question": gap.get("flashcard_q", ""),
            "answer": gap.get("flashcard_a", ""),
            "severity": gap.get("severity", "medium"),
        }
        for gap in filled_gaps
        if gap.get("flashcard_q")
    ]

    return {
        "study_guide": study_guide,
        "flashcards": flashcards,
        "status": "Study guide ready",
        "messages": [AIMessage(content=f"Generated study guide with {len(filled_gaps)} gaps and {len(flashcards)} flashcards")],
    }


def _build_study_order(gaps: list, deps: dict) -> str:
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
        label = SEVERITY_LABEL.get(severity, "Medium")
        lines.append(f"{i}. **{concept.title()}** ({label})")

    return "\n".join(lines)
