export interface AnalysisListItem {
  id: string;
  file_name: string;
  display_name: string;
  status: string;
  gap_count: number;
  filled_gap_count: number;
  created_at: string;
  raw_text_preview: string;
}

export interface GapResponse {
  id: string;
  concept: string;
  context: string;
  severity: "high" | "medium" | "low";
  explanation: string | null;
  sources: string[];
}

export interface FlashcardResponse {
  id: string;
  gap_id: string;
  concept: string;
  question: string;
  answer: string;
  severity: "high" | "medium" | "low";
  mastery: "unseen" | "unknown" | "known";
  last_reviewed: string | null;
}

export interface AnalysisDetail {
  id: string;
  file_name: string;
  display_name: string;
  status: string;
  error_message: string | null;
  study_guide: string | null;
  gap_count: number;
  filled_gap_count: number;
  created_at: string;
  updated_at: string;
  gaps: GapResponse[];
  flashcards: FlashcardResponse[];
}

export interface GraphNode {
  id: string;
  data: {
    label: string;
    severity: string;
    explanation: string;
  };
  position: { x: number; y: number };
  type?: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  animated?: boolean;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ProgressEvent {
  step: string;
  progress: number;
  message: string;
}
