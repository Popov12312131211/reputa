from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, JSON, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import APPLICATION_ID_LENGTH
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.application import Application


class ScoreResult(Base):
    __tablename__ = "score_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[str] = mapped_column(
        String(APPLICATION_ID_LENGTH),
        ForeignKey("applications.id", ondelete="CASCADE"),
        index=True,
    )
    positive_signals: Mapped[list[str]] = mapped_column(JSON, default=list)
    risk_factors: Mapped[list[str]] = mapped_column(JSON, default=list)
    stability_score: Mapped[int] = mapped_column(nullable=False)
    financial_literacy_score: Mapped[int] = mapped_column(nullable=False)
    responsibility_score: Mapped[int] = mapped_column(nullable=False)
    report_content: Mapped[str] = mapped_column(Text)
    report_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    score: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    application: Mapped["Application"] = relationship(back_populates="score_result")
