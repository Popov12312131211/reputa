import re
from datetime import date

from pydantic import BaseModel, field_validator

from app.core.constants import (
    PASSWORD_MIN_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_REGEX_UPPERCASE,
    PASSWORD_REGEX_LOWERCASE,
    PASSWORD_REGEX_DIGIT,
    PASSWORD_REGEX_SPECIAL,
    FULL_NAME_MAX_LENGTH,
    LOGIN_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    PHONE_PATTERN,
    TELEGRAM_MAX_LENGTH,
    TELEGRAM_PREFIX,
    USER_MAX_AGE_YEARS,
)


def _strip_required(v: str, empty_msg: str) -> str:
    cleaned = v.strip()
    if not cleaned:
        raise ValueError(empty_msg)
    return cleaned


class RegisterRequest(BaseModel):
    full_name: str
    birth_date: date
    login: str
    password: str
    phone: str
    telegram: str

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = _strip_required(v, "ФИО не может быть пустым")
        if len(v) > FULL_NAME_MAX_LENGTH:
            raise ValueError(f"ФИО не может превышать {FULL_NAME_MAX_LENGTH} символов")
        return v

    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        v = _strip_required(v, "Логин не может быть пустым")
        if len(v) > LOGIN_MAX_LENGTH:
            raise ValueError(f"Логин не может превышать {LOGIN_MAX_LENGTH} символов")
        return v

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: date) -> date:
        today = date.today()
        if v > today:
            raise ValueError("Дата рождения не может быть в будущем")
        # Сравнение по годам вместо дней, чтобы не вводить константу дней в году
        if v.year < today.year - USER_MAX_AGE_YEARS:
            raise ValueError("Некорректная дата рождения")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Пароль должен содержать минимум {PASSWORD_MIN_LENGTH} символов")
        if len(v) > PASSWORD_MAX_LENGTH:
            raise ValueError(f"Пароль не может превышать {PASSWORD_MAX_LENGTH} символов")
        if not re.search(PASSWORD_REGEX_UPPERCASE, v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(PASSWORD_REGEX_LOWERCASE, v):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(PASSWORD_REGEX_DIGIT, v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not re.search(PASSWORD_REGEX_SPECIAL, v):
            raise ValueError("Пароль должен содержать хотя бы один спецсимвол")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        # Дешёвая проверка длины первой, затем точный паттерн из constants
        if len(v) > PHONE_MAX_LENGTH:
            raise ValueError(f"Телефон не может превышать {PHONE_MAX_LENGTH} символов")
        if not re.match(PHONE_PATTERN, v):
            raise ValueError("Некорректный формат телефона")
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


class RegisterResponse(BaseModel):
    id: int
    full_name: str
    birth_date: date
    login: str
    phone: str
    telegram: str
    role: str


class MeResponse(BaseModel):
    id: int
    full_name: str
    role: str
