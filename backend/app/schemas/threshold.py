from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.constants import (
    MSG_THRESHOLD_OUT_OF_RANGE,
    MSG_THRESHOLD_REJECT_BELOW_APPROVE,
    SCORE_MAX,
    SCORE_MIN,
)


class ThresholdSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    auto_reject_threshold: int
    auto_approve_threshold: int


class ThresholdSettingsUpdate(BaseModel):
    auto_reject_threshold: int
    auto_approve_threshold: int

    @field_validator("auto_reject_threshold", "auto_approve_threshold")
    @classmethod
    def validate_range(cls, v: int) -> int:
        # Порог обязан лежать в шкале оценки 0–100 (см. PRODUCT.md).
        if v < SCORE_MIN or v > SCORE_MAX:
            raise ValueError(MSG_THRESHOLD_OUT_OF_RANGE)
        return v

    @model_validator(mode="after")
    def validate_order(self) -> "ThresholdSettingsUpdate":
        # Инвариант APP-003: при reject >= approve авто-одобрение становится
        # недостижимым (первая ветка decide_auto_status всегда побеждает).
        if self.auto_reject_threshold >= self.auto_approve_threshold:
            raise ValueError(MSG_THRESHOLD_REJECT_BELOW_APPROVE)
        return self
