from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.core.constants import THRESHOLD_SETTINGS_ID


class ThresholdSettings(Base):
    """Настройки пороговой автообработки. Синглтон: всегда одна строка (id=1).

    Хранятся в БД и редактируются сотрудником (EMP-002), а не захардкожены.
    """

    __tablename__ = "threshold_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=THRESHOLD_SETTINGS_ID)
    auto_reject_threshold: Mapped[int] = mapped_column(nullable=False)
    auto_approve_threshold: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())