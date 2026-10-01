from typing import TypedDict, List, Annotated
from langgraph.graph.message import add_messages


class Gap(TypedDict):
    concept: str
    context: str
    severity: str
    explanation: str
    flashcard_q: str
    flashcard_a: str
    sources: List[str]


class GapFinderState(TypedDict):
    file_name: str
    raw_text: str
    analysis_id: str

    all_concepts: List[str]
    gaps: List[Gap]
    prioritized_gaps: List[Gap]
    filled_gaps: List[Gap]
    concept_dependencies: dict

    study_guide: str
    flashcards: List[dict]

    status: str
    messages: Annotated[list, add_messages]
