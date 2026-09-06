from datetime import datetime
from decimal import Decimal
from enum import Enum

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
    telegram_channel: str = ""

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
        v = (v or "").strip()
        if v and not v.startswith(TELEGRAM_PREFIX):
            raise ValueError("Телеграм-канал должен начинаться с @")
        if len(v) > TELEGRAM_CHANNEL_MAX_LENGTH:
            raise ValueError(
                f"Телеграм-канал не может превышать {TELEGRAM_CHANNEL_MAX_LENGTH} символов"
            )
        return v


class ApplicationDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


class ApplicationDecisionRequest(BaseModel):
    decision: ApplicationDecision


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    amount: Decimal
    purpose: str
    telegram: str
    telegram_channel: str
    status: str
    score: int | None = None
    created_at: datetime | None = None


class ApplicationDetailResponse(ApplicationResponse):
    """Детальная карточка заявки (APP-005). Добавляет ФИО заёмщика для шапки."""

    full_name: str


class ApplicationListItemResponse(ApplicationResponse):
    """Строка списка всех заявок для сотрудника (EMP-004). Добавляет ФИО
    заёмщика из связанной таблицы users для таблицы /employee/application."""

    full_name: str


class ScoreResultResponse(BaseModel):
    """Результат скоринга заявки (EMP-005): позитивные сигналы, факторы риска,
    психологический портрет (три метрики 0–10) и отчёт для кредитного комитета.
    Может отсутствовать у заявки, пока пайплайн STMT-002/TG-003 не заполнил результат."""

    model_config = ConfigDict(from_attributes=True)

    positive_signals: list[str]
    risk_factors: list[str]
    stability_score: int
    financial_literacy_score: int
    responsibility_score: int
    report_content: str
    report_updated_at: datetime | None = None
    score: int


class EmployeePublic(BaseModel):
    """Краткая карточка сотрудника (EMP-005): ФИО и логин сотрудника,
    принявшего решение по заявке."""

    model_config = ConfigDict(from_attributes=True)

    login: str
    full_name: str


class EmployeeApplicationDetailResponse(ApplicationDetailResponse):
    """Детальная карточка заявки сотрудника (EMP-005). То же, что видит
    заёмщик (APP-005), плюс полный разбор скоринга, недоступный заёмщику."""

    score_result: ScoreResultResponse | None = None
    decided_by_employee: EmployeePublic | None = None