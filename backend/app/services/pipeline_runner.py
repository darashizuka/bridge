import asyncio
import logging
import uuid
from typing import Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models import Analysis, Concept, Gap, Flashcard, Dependency

logger = logging.getLogger(__name__)

progress_channels: Dict[str, asyncio.Queue] = {}

STEP_PROGRESS = {
    "parse": ("parsing", 0.10, "Extracting text and identifying concepts..."),
    "gap_detect": ("detecting", 0.30, "Detecting knowledge gaps..."),
    "prioritize": ("prioritizing", 0.45, "Ranking gaps by importance..."),
    "fill": ("filling", 0.60, "Searching the web and filling gaps..."),
    "connect": ("connecting", 0.80, "Mapping concept dependencies..."),
    "output": ("outputting", 0.90, "Generating study guide and flashcards..."),
}


async def _emit(analysis_id: str, step: str, progress: float, message: str):
    queue = progress_channels.get(analysis_id)
    if queue:
        await queue.put({"step": step, "progress": progress, "message": message})


async def _update_status(analysis_id: str, status: str, error: str | None = None):
    async with async_session() as session:
        result = await session.execute(select(Analysis).where(Analysis.id == analysis_id))
        analysis = result.scalar_one_or_none()
        if analysis:
            analysis.status = status
            if error:
                analysis.error_message = error
            await session.commit()


async def _save_results(analysis_id: str, final_state: dict):
    async with async_session() as session:
        result = await session.execute(select(Analysis).where(Analysis.id == analysis_id))
        analysis = result.scalar_one_or_none()
        if not analysis:
            return

        filled_gaps = final_state.get("filled_gaps", [])
        all_gaps = final_state.get("prioritized_gaps", final_state.get("gaps", []))
        concept_deps = final_state.get("concept_dependencies", {})
        all_concepts = final_state.get("all_concepts", [])

        analysis.study_guide = final_state.get("study_guide", "")
        analysis.gap_count = len(all_gaps)
        analysis.filled_gap_count = len(filled_gaps)
        analysis.status = "completed"

        concept_map = {}
        for name in all_concepts:
            concept = Concept(id=str(uuid.uuid4()), analysis_id=analysis_id, name=name)
            session.add(concept)
            concept_map[name.lower()] = concept

        for gap_data in filled_gaps:
            gap_id = str(uuid.uuid4())
            gap = Gap(
                id=gap_id,
                analysis_id=analysis_id,
                concept=gap_data.get("concept", ""),
                context=gap_data.get("context", ""),
                severity=gap_data.get("severity", "medium"),
                explanation=gap_data.get("explanation"),
                sources=gap_data.get("sources", []),
            )
            session.add(gap)

            q = gap_data.get("flashcard_q", "")
            a = gap_data.get("flashcard_a", "")
            if q:
                flashcard = Flashcard(
                    id=str(uuid.uuid4()),
                    gap_id=gap_id,
                    analysis_id=analysis_id,
                    concept=gap_data.get("concept", ""),
                    question=q,
                    answer=a,
                    severity=gap_data.get("severity", "medium"),
                )
                session.add(flashcard)

        await session.flush()

        for concept_name, prereqs in concept_deps.items():
            concept_obj = concept_map.get(concept_name.lower())
            if not concept_obj:
                continue
            for prereq_name in prereqs:
                prereq_obj = concept_map.get(prereq_name.lower())
                if not prereq_obj:
                    continue
                dep = Dependency(
                    id=str(uuid.uuid4()),
                    analysis_id=analysis_id,
                    concept_id=concept_obj.id,
                    prerequisite_id=prereq_obj.id,
                )
                session.add(dep)

        await session.commit()


async def run_pipeline(analysis_id: str, raw_text: str, file_name: str):
    queue = asyncio.Queue()
    progress_channels[analysis_id] = queue

    try:
        await _emit(analysis_id, "pending", 0.05, "Starting analysis...")
        await _update_status(analysis_id, "parsing")

        from app.pipeline.graph import build_graph

        graph = build_graph()
        initial_state = {
            "file_name": file_name,
            "raw_text": raw_text,
            "analysis_id": analysis_id,
            "all_concepts": [],
            "gaps": [],
            "prioritized_gaps": [],
            "filled_gaps": [],
            "concept_dependencies": {},
            "study_guide": "",
            "flashcards": [],
            "status": "Starting...",
            "messages": [],
        }

        final_state = initial_state
        async for step in graph.astream(initial_state):
            node_name = list(step.keys())[0]
            final_state.update(step[node_name])

            if node_name in STEP_PROGRESS:
                status, progress, message = STEP_PROGRESS[node_name]
                await _emit(analysis_id, status, progress, message)
                await _update_status(analysis_id, status)

        await _save_results(analysis_id, final_state)
        await _emit(analysis_id, "completed", 1.0, "Analysis complete")

    except Exception as e:
        logger.exception(f"Pipeline failed for analysis {analysis_id}")
        await _update_status(analysis_id, "failed", str(e))
        await _emit(analysis_id, "failed", -1, str(e))

    finally:
        await asyncio.sleep(30)
        progress_channels.pop(analysis_id, None)
