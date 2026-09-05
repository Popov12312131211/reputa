import re

from app.core.constants import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    PASSWORD_REGEX_DIGIT,
    PASSWORD_REGEX_LOWERCASE,
    PASSWORD_REGEX_SPECIAL,
    PASSWORD_REGEX_UPPERCASE,
    PHONE_MAX_LENGTH,
    PHONE_PATTERN,
    TELEGRAM_MAX_LENGTH,
    TELEGRAM_PREFIX,
)


def _strip_required(v: str, empty_msg: str) -> str:
    cleaned = v.strip()
    if not cleaned:
        raise ValueError(empty_msg)
    return cleaned


def validate_password(v: str) -> str:
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


def validate_phone(v: str) -> str:
    v = v.strip()
    if len(v) > PHONE_MAX_LENGTH:
        raise ValueError(f"Телефон не может превышать {PHONE_MAX_LENGTH} символов")
    if not re.match(PHONE_PATTERN, v):
        raise ValueError("Некорректный формат телефона")
    return v


def validate_telegram(v: str) -> str:
    v = v.strip()
    if not v.startswith(TELEGRAM_PREFIX):
        raise ValueError("Телеграм должен начинаться с @")
    if len(v) > TELEGRAM_MAX_LENGTH:
        raise ValueError(f"Телеграм не может превышать {TELEGRAM_MAX_LENGTH} символов")
    return v