from pydantic import BaseModel, field_validator

from app.core.constants import (
    FULL_NAME_MAX_LENGTH,
    LOGIN_MAX_LENGTH,
)
from app.schemas.validators import (
    _strip_required,
    validate_password,
    validate_phone,
    validate_telegram,
)


class ProfileUpdateRequest(BaseModel):
    full_name: str
    login: str
    phone: str
    telegram: str
    password: str | None = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = _strip_required(value, "ФИО не может быть пустым")
        if len(value) > FULL_NAME_MAX_LENGTH:
            raise ValueError(f"ФИО не может превышать {FULL_NAME_MAX_LENGTH} символов")
        return value

    @field_validator("login")
    @classmethod
    def validate_login(cls, value: str) -> str:
        value = _strip_required(value, "Логин не может быть пустым")
        if len(value) > LOGIN_MAX_LENGTH:
            raise ValueError(f"Логин не может превышать {LOGIN_MAX_LENGTH} символов")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return validate_phone(value)

    @field_validator("telegram")
    @classmethod
    def validate_telegram(cls, value: str) -> str:
        return validate_telegram(value)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return validate_password(value)


class ProfileResponse(BaseModel):
    id: int
    full_name: str
    login: str
    phone: str
    telegram: str
    role: str