from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User, UserRole
from app.models.application import Application, ApplicationStatus
from app.core.constants import (
    APPLICATION_STATUS_IN_QUEUE,
    APPLICATION_STATUS_AUTO_APPROVED,
    APPLICATION_STATUS_AUTO_REJECTED,
    APPLICATION_STATUS_EMPLOYEE_APPROVED,
    APPLICATION_STATUS_EMPLOYEE_REJECTED,
    SCORE_MIN,
    SCORE_MAX,
)


def _make_engine_and_user(db):
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
    return user


def test_application_status_constants():
    assert ApplicationStatus.IN_QUEUE.value == APPLICATION_STATUS_IN_QUEUE == "in_queue"
    assert ApplicationStatus.AUTO_APPROVED.value == APPLICATION_STATUS_AUTO_APPROVED
    assert ApplicationStatus.AUTO_REJECTED.value == APPLICATION_STATUS_AUTO_REJECTED
    assert ApplicationStatus.EMPLOYEE_APPROVED.value == APPLICATION_STATUS_EMPLOYEE_APPROVED
    assert ApplicationStatus.EMPLOYEE_REJECTED.value == APPLICATION_STATUS_EMPLOYEE_REJECTED


def test_score_bounds():
    assert SCORE_MIN == 0
    assert SCORE_MAX == 100
    assert SCORE_MAX > SCORE_MIN


def test_application_model_roundtrip_with_user():
    engine = create_engine("sqlite:///:memory:")
    testing_session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    db = testing_session()
    user = _make_engine_and_user(db)

    app = Application(
        user_id=user.id,
        amount=Decimal("50000.00"),
        purpose="Ремонт квартиры",
        telegram="@ivan",
        telegram_channel="@ivan_channel",
        status=ApplicationStatus.IN_QUEUE.value,
        score=72,
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    assert app.id is not None
    assert app.user_id == user.id
    assert app.amount == Decimal("50000.00")
    assert app.purpose == "Ремонт квартиры"
    assert app.telegram == "@ivan"
    assert app.telegram_channel == "@ivan_channel"
    assert app.status == APPLICATION_STATUS_IN_QUEUE
    assert app.score == 72

    db.close()
    engine.dispose()


def test_application_relationship_and_foreign_key():
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    db = testing_session()
    user = _make_engine_and_user(db)

    app = Application(
        user_id=user.id,
        amount=Decimal("100000.00"),
        purpose="Кредит",
        telegram="@ivan",
        telegram_channel="@ivan_channel",
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    assert app.user is not None
    assert app.user.login == "ivan"
    assert user.applications[0].id == app.id

    db.close()
    engine.dispose()
