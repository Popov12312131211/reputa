import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.core.constants import (
    FULL_NAME_MAX_LENGTH,
    LOGIN_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    TELEGRAM_MAX_LENGTH,
    PASSWORD_HASH_MAX_LENGTH,
    ROLE_USER,
    ROLE_EMPLOYEE,
    ROLE_MAX_LENGTH,
)

if TYPE_CHECKING:
    from app.models.application import Application


class UserRole(str, enum.Enum):
    USER = ROLE_USER
    EMPLOYEE = ROLE_EMPLOYEE


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(FULL_NAME_MAX_LENGTH))
    birth_date: Mapped[date] = mapped_column(Date)
    login: Mapped[str] = mapped_column(String(LOGIN_MAX_LENGTH), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(PASSWORD_HASH_MAX_LENGTH))
    phone: Mapped[str] = mapped_column(String(PHONE_MAX_LENGTH))
    telegram: Mapped[str] = mapped_column(String(TELEGRAM_MAX_LENGTH))
    role: Mapped[str] = mapped_column(String(ROLE_MAX_LENGTH), default=UserRole.USER.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    applications: Mapped[list["Application"]] = relationship(
        back_populates="user",
        # Каскад удаления заявок выполняет сама БД (users.id -> applications.user_id
        # объявлен с ON DELETE CASCADE). Без passive_deletes SQLAlchemy пытался бы
        # обнулить user_id у заявок перед удалением пользователя — а колонка NOT NULL,
        # что падало бы с IntegrityError при удалении аккаунта.
        passive_deletes=True,
    )
