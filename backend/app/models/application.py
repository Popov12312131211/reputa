import enum
import hashlib
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.core.constants import (
    AMOUNT_PRECISION,
    AMOUNT_SCALE,
    APPLICATION_ID_LENGTH,
    PURPOSE_MAX_LENGTH,
    TELEGRAM_CHANNEL_MAX_LENGTH,
    TELEGRAM_MAX_LENGTH,
    APPLICATION_STATUS_IN_QUEUE,
    APPLICATION_STATUS_MAX_LENGTH,
)

if TYPE_CHECKING:
    from app.models.score_result import ScoreResult
    from app.models.user import User


def generate_application_id() -> str:
    """Строковый ID заявки (INFRA-004): первые 10-12 символов sha256-хеша от
    случайного uuid4. Не автоинкремент и не предсказуемая последовательность —
    каждый ID случаен и не зависит от предыдущих/количества записей."""
    return hashlib.sha256(uuid.uuid4().hex.encode("ascii")).hexdigest()[:APPLICATION_ID_LENGTH]


class ApplicationStatus(str, enum.Enum):
    IN_QUEUE = APPLICATION_STATUS_IN_QUEUE
    AUTO_APPROVED = "auto_approved"
    AUTO_REJECTED = "auto_rejected"
    EMPLOYEE_APPROVED = "employee_approved"
    EMPLOYEE_REJECTED = "employee_rejected"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(
        String(APPLICATION_ID_LENGTH), primary_key=True, default=generate_application_id
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(AMOUNT_PRECISION, AMOUNT_SCALE)
    )
    purpose: Mapped[str] = mapped_column(String(PURPOSE_MAX_LENGTH))
    telegram: Mapped[str] = mapped_column(String(TELEGRAM_MAX_LENGTH))
    telegram_channel: Mapped[str] = mapped_column(String(TELEGRAM_CHANNEL_MAX_LENGTH))
    status: Mapped[str] = mapped_column(
        String(APPLICATION_STATUS_MAX_LENGTH),
        default=ApplicationStatus.IN_QUEUE.value,
        server_default=APPLICATION_STATUS_IN_QUEUE,
    )
    score: Mapped[int | None] = mapped_column(nullable=True)
    decided_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(
        back_populates="applications", foreign_keys=[user_id]
    )
    decided_by_user: Mapped["User | None"] = relationship(
        foreign_keys=[decided_by]
    )
    score_result: Mapped["ScoreResult | None"] = relationship(back_populates="application", uselist=False)
