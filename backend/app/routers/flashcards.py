import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_current_user
from app.database import get_db
from app.models import Flashcard, Analysis
from app.schemas import FlashcardResponse, FlashcardUpdate

router = APIRouter()


@router.get("/analyses/{analysis_id}/flashcards", response_model=list[FlashcardResponse])
async def get_flashcards(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    analysis = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user_id)
    )
    if not analysis.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Analysis not found.")

    result = await db.execute(
        select(Flashcard).where(Flashcard.analysis_id == analysis_id)
    )
    return result.scalars().all()


@router.patch("/analyses/{analysis_id}/flashcards/{flashcard_id}", response_model=FlashcardResponse)
async def update_flashcard_mastery(
    analysis_id: str,
    flashcard_id: str,
    body: FlashcardUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    analysis = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user_id)
    )
    if not analysis.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Analysis not found.")

    result = await db.execute(
        select(Flashcard).where(Flashcard.id == flashcard_id, Flashcard.analysis_id == analysis_id)
    )
    flashcard = result.scalar_one_or_none()
    if not flashcard:
        raise HTTPException(status_code=404, detail="Flashcard not found.")

    flashcard.mastery = body.mastery
    flashcard.last_reviewed = datetime.datetime.now(datetime.timezone.utc)
    await db.commit()
    await db.refresh(flashcard)
    return flashcard
