from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User, UserRole
from app.core.constants import (
    ROLE_USER,
    ROLE_EMPLOYEE,
    PASSWORD_MIN_LENGTH,
    PASSWORD_MAX_LENGTH,
)


def test_user_role_constants():
    assert UserRole.USER.value == ROLE_USER == "user"
    assert UserRole.EMPLOYEE.value == ROLE_EMPLOYEE == "employee"


def test_password_length_limits():
    assert 8 <= PASSWORD_MIN_LENGTH
    assert PASSWORD_MAX_LENGTH >= PASSWORD_MIN_LENGTH


def test_user_model_roundtrip():
    engine = create_engine("sqlite:///:memory:")
    testing_session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    db = testing_session()
    user = User(
        full_name="Иван Петров",
        birth_date=date(1995, 5, 20),
        login="ivan",
        password_hash="hash",
        phone="+79990000000",
        telegram="@ivan",
        role=UserRole.USER.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.full_name == "Иван Петров"
    assert user.birth_date == date(1995, 5, 20)
    assert user.login == "ivan"
    assert user.role == ROLE_USER

    db.close()
    engine.dispose()
