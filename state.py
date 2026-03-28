from typing import TypedDict, List, Optional, Annotated
from langgraph.graph.message import add_messages


class Gap(TypedDict):
    concept: str          # The term/concept
    context: str          # Sentence where it appeared
    severity: str         # "high" | "medium" | "low"
    explanation: str      # Filled explanation
    flashcard_q: str      # Flashcard question
    flashcard_a: str      # Flashcard answer
    sources: List[str]    # URLs found


class GapFinderState(TypedDict):
    # --- Input ---
    file_name: str
    raw_text: str                        # Full extracted text from file

    # --- Node Outputs ---
    all_concepts: List[str]              # Every concept found in notes
    gaps: List[Gap]                      # Unfilled gaps detected
    prioritized_gaps: List[Gap]          # Gaps ranked by severity
    filled_gaps: List[Gap]               # Gaps with explanations added
    concept_dependencies: dict           # { concept: [depends_on, ...] }

    # --- Final Output ---
    study_guide: str                     # Markdown study guide
    flashcards: List[dict]               # [{q, a, concept}, ...]

    # --- Progress Tracking ---
    status: str                          # Current step label
    messages: Annotated[list, add_messages]
