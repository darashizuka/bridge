import asyncio
import json
import os
import uuid
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import User, Analysis, Gap, Flashcard, Concept, Dependency
from app.schemas import (
    AnalysisListItem, AnalysisDetail, AnalysisRename, AnalysisCreate,
    GapResponse, FlashcardResponse, GraphNode, GraphEdge, GraphResponse,
)
from app.services.file_parser import extract_text_from_file, validate_file_extension
from app.services.pipeline_runner import run_pipeline, progress_channels

router = APIRouter()
settings = get_settings()


@router.post("/analyses")
async def create_analysis(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    file_name: str | None = Form(None),
):
    if not file and not text:
        raise HTTPException(status_code=400, detail="Provide either a file or text.")

    raw_text = ""
    name = file_name or "pasted_notes.txt"

    if file:
        if not validate_file_extension(file.filename or ""):
            raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, PPTX, or TXT.")

        content = await file.read()
        if len(content) > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_file_size_mb}MB limit.")

        suffix = os.path.splitext(file.filename or ".txt")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            raw_text = extract_text_from_file(tmp_path)
        finally:
            os.unlink(tmp_path)

        name = file.filename or name
    else:
        raw_text = text or ""

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text.")

    if len(raw_text) > settings.max_text_chars:
        raise HTTPException(
            status_code=413,
            detail=f"Text exceeds {settings.max_text_chars:,} character limit ({len(raw_text):,} chars extracted).",
        )

    existing_user = await db.execute(select(User).where(User.id == user_id))
    if not existing_user.scalar_one_or_none():
        db.add(User(id=user_id))
        await db.flush()

    analysis_id = str(uuid.uuid4())
    analysis = Analysis(
        id=analysis_id,
        user_id=user_id,
        file_name=name,
        display_name=os.path.splitext(name)[0],
        raw_text_preview=raw_text[:500],
        status="pending",
    )
    db.add(analysis)
    await db.commit()

    background_tasks.add_task(run_pipeline, analysis_id, raw_text, name)

    return {"id": analysis_id, "status": "pending"}


@router.get("/analyses", response_model=list[AnalysisListItem])
async def list_analyses(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    search: str | None = None,
    page: int = 1,
    limit: int = 20,
):
    query = select(Analysis).where(Analysis.user_id == user_id)
    if search:
        query = query.where(Analysis.display_name.ilike(f"%{search}%"))
    query = query.order_by(Analysis.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/analyses/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    result = await db.execute(
        select(Analysis)
        .where(Analysis.id == analysis_id, Analysis.user_id == user_id)
        .options(selectinload(Analysis.gaps).selectinload(Gap.flashcard))
        .options(selectinload(Analysis.flashcards))
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    gaps = [
        GapResponse(
            id=g.id, concept=g.concept, context=g.context,
            severity=g.severity, explanation=g.explanation, sources=g.sources or [],
        )
        for g in analysis.gaps
    ]
    flashcards = [
        FlashcardResponse(
            id=f.id, gap_id=f.gap_id, concept=f.concept, question=f.question,
            answer=f.answer, severity=f.severity, mastery=f.mastery,
            last_reviewed=f.last_reviewed,
        )
        for f in analysis.flashcards
    ]

    return AnalysisDetail(
        id=analysis.id,
        file_name=analysis.file_name,
        display_name=analysis.display_name,
        status=analysis.status,
        error_message=analysis.error_message,
        study_guide=analysis.study_guide,
        gap_count=analysis.gap_count,
        filled_gap_count=analysis.filled_gap_count,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
        gaps=gaps,
        flashcards=flashcards,
    )


@router.patch("/analyses/{analysis_id}")
async def rename_analysis(
    analysis_id: str,
    body: AnalysisRename,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    analysis.display_name = body.display_name
    await db.commit()
    return {"id": analysis.id, "display_name": analysis.display_name}


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    await db.delete(analysis)
    await db.commit()
    return {"ok": True}


@router.get("/analyses/{analysis_id}/progress")
async def analysis_progress(
    analysis_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    async def event_stream():
        if analysis.status in ("completed", "failed"):
            data = json.dumps({"step": analysis.status, "progress": 1.0 if analysis.status == "completed" else -1, "message": analysis.error_message or "Done"})
            yield f"data: {data}\n\n"
            return

        queue = progress_channels.get(analysis_id)
        if not queue:
            data = json.dumps({"step": analysis.status, "progress": 0.5, "message": "Processing..."})
            yield f"data: {data}\n\n"
            return

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=60)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("step") in ("completed", "failed"):
                    break
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'step': 'heartbeat', 'progress': -1, 'message': 'Still processing...'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/analyses/{analysis_id}/graph", response_model=GraphResponse)
async def get_graph(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    concepts_result = await db.execute(
        select(Concept).where(Concept.analysis_id == analysis_id)
    )
    concepts = concepts_result.scalars().all()

    gaps_result = await db.execute(
        select(Gap).where(Gap.analysis_id == analysis_id)
    )
    gaps = {g.concept.lower(): g for g in gaps_result.scalars().all()}

    deps_result = await db.execute(
        select(Dependency).where(Dependency.analysis_id == analysis_id)
    )
    deps = deps_result.scalars().all()

    concept_map = {c.id: c for c in concepts}

    gap_concept_names = set(gaps.keys())
    relevant_concepts = [c for c in concepts if c.name.lower() in gap_concept_names]

    nodes = []
    for c in relevant_concepts:
        gap = gaps.get(c.name.lower())
        nodes.append(GraphNode(
            id=c.id,
            data={
                "label": c.name,
                "severity": gap.severity if gap else "medium",
                "explanation": gap.explanation[:200] if gap and gap.explanation else "",
            },
        ))

    edges = []
    node_ids = {n.id for n in nodes}
    for d in deps:
        if d.concept_id in node_ids and d.prerequisite_id in node_ids:
            edges.append(GraphEdge(
                id=d.id,
                source=d.prerequisite_id,
                target=d.concept_id,
            ))

    return GraphResponse(nodes=nodes, edges=edges)
