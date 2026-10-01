from pydantic import BaseModel, Field
from datetime import datetime


class AnalysisCreate(BaseModel):
    text: str | None = None
    file_name: str = "pasted_notes.txt"


class AnalysisListItem(BaseModel):
    id: str
    file_name: str
    display_name: str
    status: str
    gap_count: int
    filled_gap_count: int
    created_at: datetime
    raw_text_preview: str

    model_config = {"from_attributes": True}


class GapResponse(BaseModel):
    id: str
    concept: str
    context: str
    severity: str
    explanation: str | None
    sources: list[str]

    model_config = {"from_attributes": True}


class FlashcardResponse(BaseModel):
    id: str
    gap_id: str
    concept: str
    question: str
    answer: str
    severity: str
    mastery: str
    last_reviewed: datetime | None

    model_config = {"from_attributes": True}


class FlashcardUpdate(BaseModel):
    mastery: str = Field(pattern="^(unseen|unknown|known)$")


class GraphNode(BaseModel):
    id: str
    data: dict
    position: dict = {"x": 0, "y": 0}
    type: str = "default"


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    animated: bool = True


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class AnalysisDetail(BaseModel):
    id: str
    file_name: str
    display_name: str
    status: str
    error_message: str | None
    study_guide: str | None
    gap_count: int
    filled_gap_count: int
    created_at: datetime
    updated_at: datetime
    gaps: list[GapResponse]
    flashcards: list[FlashcardResponse]

    model_config = {"from_attributes": True}


class AnalysisRename(BaseModel):
    display_name: str = Field(min_length=1, max_length=200)


class ProgressEvent(BaseModel):
    step: str
    progress: float
    message: str
