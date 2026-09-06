from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmployeeThresholds(Base):
    """Персональные пороги автообработки сотрудника (APP-008).

    В отличие от прежнего синглтона `threshold_settings`, каждый сотрудник
    хранит собственные пороги авто-отклонения/авто-одобрения. Один сотрудник —
    одна строка (user_id — первичный ключ). Редактируются в EMP-002 через
    /api/employee/settings (API сохранено).
    """

    __tablename__ = "employee_thresholds"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    auto_reject_threshold: Mapped[int] = mapped_column(nullable=False)
    auto_approve_threshold: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def id(self) -> int:
        # API /employee/settings сохранён (EMP-002): ответ содержит поле id,
        # которое для персональных порогов совпадает с идентификатором сотрудника.
        return self.user_id
