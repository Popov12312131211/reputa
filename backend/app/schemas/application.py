from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.constants import (
    AMOUNT_MIN_VALUE,
    PURPOSE_MAX_LENGTH,
    TELEGRAM_CHANNEL_MAX_LENGTH,
    TELEGRAM_MAX_LENGTH,
    TELEGRAM_PREFIX,
)
from app.schemas.validators import _strip_required


class ApplicationCreate(BaseModel):
    amount: Decimal
    purpose: str
    telegram: str
    telegram_channel: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= AMOUNT_MIN_VALUE:
            raise ValueError("Сумма должна быть больше нуля")
        return v

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        v = _strip_required(v, "Цель кредита не может быть пустой")
        if len(v) > PURPOSE_MAX_LENGTH:
            raise ValueError(f"Цель кредита не может превышать {PURPOSE_MAX_LENGTH} символов")
        return v

    @field_validator("telegram")
    @classmethod
    def validate_telegram(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(TELEGRAM_PREFIX):
            raise ValueError("Телеграм должен начинаться с @")
        if len(v) > TELEGRAM_MAX_LENGTH:
            raise ValueError(f"Телеграм не может превышать {TELEGRAM_MAX_LENGTH} символов")
        return v

    @field_validator("telegram_channel")
    @classmethod
    def validate_telegram_channel(cls, v: str) -> str:
        v = _strip_required(v, "Телеграм-канал не может быть пустым")
        if not v.startswith(TELEGRAM_PREFIX):
            raise ValueError("Телеграм-канал должен начинаться с @")
        if len(v) > TELEGRAM_CHANNEL_MAX_LENGTH:
            raise ValueError(
                f"Телеграм-канал не может превышать {TELEGRAM_CHANNEL_MAX_LENGTH} символов"
            )
        return v


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    amount: Decimal
    purpose: str
    telegram: str
    telegram_channel: str
    status: str
    score: int | None = None
    created_at: datetime | None = None