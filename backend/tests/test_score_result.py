from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.user import User, UserRole
from app.models.application import Application
from app.models.score_result import ScoreResult
from app.core.constants import (
    PORTRAIT_METRIC_MIN,
    PORTRAIT_METRIC_MAX,
    SCORE_MIN,
    SCORE_MAX,
)


def _make_user_and_application(db):
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

    app = Application(
        user_id=user.id,
        amount=Decimal("50000.00"),
        purpose="Ремонт квартиры",
        telegram="@ivan",
        telegram_channel="@ivan_channel",
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return user, app


def test_portrait_metrics_bounds():
    assert PORTRAIT_METRIC_MIN == 0
    assert PORTRAIT_METRIC_MAX == 10
    assert PORTRAIT_METRIC_MAX > PORTRAIT_METRIC_MIN


def test_score_bounds():
    assert SCORE_MIN == 0
    assert SCORE_MAX == 100
    assert SCORE_MAX > SCORE_MIN


def test_score_result_model_roundtrip():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    db = testing_session()
    _, app = _make_user_and_application(db)

    res = ScoreResult(
        application_id=app.id,
        positive_signals=["Регулярные поступления", "Низкая доля трат на развлечения"],
        risk_factors=["Небольшой средний остаток"],
        stability_score=8,
        financial_literacy_score=7,
        responsibility_score=9,
        report_content="Отчёт для кредитного комитета по заявке.",
        score=78,
    )
    db.add(res)
    db.commit()
    db.refresh(res)

    assert res.id is not None
    assert res.application_id == app.id
    assert res.positive_signals == ["Регулярные поступления", "Низкая доля трат на развлечения"]
    assert res.risk_factors == ["Небольшой средний остаток"]
    assert res.stability_score == 8
    assert res.financial_literacy_score == 7
    assert res.responsibility_score == 9
    assert res.report_content == "Отчёт для кредитного комитета по заявке."
    assert res.report_updated_at is not None
    assert isinstance(res.report_updated_at, datetime)
    assert res.score == 78

    db.close()
    engine.dispose()


def test_score_result_relationship_with_application():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    db = testing_session()
    _, app = _make_user_and_application(db)

    res = ScoreResult(
        application_id=app.id,
        positive_signals=["Сигнал"],
        risk_factors=["Фактор"],
        stability_score=5,
        financial_literacy_score=6,
        responsibility_score=5,
        report_content="Отчёт.",
        score=60,
    )
    db.add(res)
    db.commit()
    db.refresh(res)

    assert res.application is not None
    assert res.application.id == app.id
    assert app.score_result.id == res.id
    assert isinstance(res.positive_signals, list)

    db.close()
    engine.dispose()
