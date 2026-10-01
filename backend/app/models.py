import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc)
    )

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    file_name: Mapped[str] = mapped_column(String)
    display_name: Mapped[str] = mapped_column(String)
    raw_text_preview: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    study_guide: Mapped[str | None] = mapped_column(Text, nullable=True)
    gap_count: Mapped[int] = mapped_column(Integer, default=0)
    filled_gap_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="analyses")
    concepts: Mapped[list["Concept"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    gaps: Mapped[list["Gap"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    flashcards: Mapped[list["Flashcard"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_analyses_user_created", "user_id", created_at.desc()),)


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String)

    analysis: Mapped["Analysis"] = relationship(back_populates="concepts")
    depended_on_by: Mapped[list["Dependency"]] = relationship(
        back_populates="prerequisite", foreign_keys="Dependency.prerequisite_id", cascade="all, delete-orphan"
    )
    depends_on: Mapped[list["Dependency"]] = relationship(
        back_populates="concept", foreign_keys="Dependency.concept_id", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("analysis_id", "name"),)


class Gap(Base):
    __tablename__ = "gaps"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"))
    concept: Mapped[str] = mapped_column(String)
    context: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String, default="medium")
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    analysis: Mapped["Analysis"] = relationship(back_populates="gaps")
    flashcard: Mapped["Flashcard | None"] = relationship(back_populates="gap", uselist=False)

    __table_args__ = (Index("ix_gaps_analysis", "analysis_id"),)


class Flashcard(Base):
    __tablename__ = "flashcards"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    gap_id: Mapped[str] = mapped_column(ForeignKey("gaps.id", ondelete="CASCADE"), unique=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"))
    concept: Mapped[str] = mapped_column(String)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String, default="medium")
    mastery: Mapped[str] = mapped_column(String, default="unseen")
    last_reviewed: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    gap: Mapped["Gap"] = relationship(back_populates="flashcard")
    analysis: Mapped["Analysis"] = relationship(back_populates="flashcards")

    __table_args__ = (Index("ix_flashcards_analysis", "analysis_id"),)


class Dependency(Base):
    __tablename__ = "dependencies"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"))
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"))
    prerequisite_id: Mapped[str] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"))

    concept: Mapped["Concept"] = relationship(back_populates="depends_on", foreign_keys=[concept_id])
    prerequisite: Mapped["Concept"] = relationship(back_populates="depended_on_by", foreign_keys=[prerequisite_id])

    __table_args__ = (
        UniqueConstraint("concept_id", "prerequisite_id"),
        Index("ix_dependencies_analysis", "analysis_id"),
    )
