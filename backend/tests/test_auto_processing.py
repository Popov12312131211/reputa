from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.core.constants import (
    APPLICATION_STATUS_AUTO_APPROVED,
    APPLICATION_STATUS_AUTO_REJECTED,
    APPLICATION_STATUS_IN_QUEUE,
    AUTO_APPROVE_THRESHOLD_DEFAULT,
    AUTO_REJECT_THRESHOLD_DEFAULT,
    THRESHOLD_SETTINGS_ID,
    SCORE_MIN,
    SCORE_MAX,
)
from app.models.application import Application
from app.models.threshold_settings import ThresholdSettings
from app.models.user import User, UserRole
from app.services.auto_processing import (
    apply_auto_decision,
    decide_auto_status,
    get_threshold_settings,
)


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    return engine, session


def _make_application(db, score=None, login="ivan"):
    user = User(
        full_name="Иван Петров",
        birth_date=date(1995, 5, 20),
        login=login,
        password_hash="hash",
        phone="+79990000000",
        telegram="@ivan",
        role=UserRole.USER.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    application = Application(
        user_id=user.id,
        amount=Decimal("50000.00"),
        purpose="Ремонт квартиры",
        telegram="@ivan",
        telegram_channel="@ivan_channel",
        status=APPLICATION_STATUS_IN_QUEUE,
        score=score,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def _settings(reject=AUTO_REJECT_THRESHOLD_DEFAULT, approve=AUTO_APPROVE_THRESHOLD_DEFAULT):
    return ThresholdSettings(
        id=THRESHOLD_SETTINGS_ID,
        auto_reject_threshold=reject,
        auto_approve_threshold=approve,
    )


def test_threshold_defaults_are_within_score_range():
    assert SCORE_MIN <= AUTO_REJECT_THRESHOLD_DEFAULT < AUTO_APPROVE_THRESHOLD_DEFAULT <= SCORE_MAX


class TestDecideAutoStatus:
    def test_score_below_reject_threshold(self):
        assert decide_auto_status(10, _settings(30, 70)) == APPLICATION_STATUS_AUTO_REJECTED

    def test_score_equal_to_reject_threshold(self):
        assert decide_auto_status(30, _settings(30, 70)) == APPLICATION_STATUS_AUTO_REJECTED

    def test_score_one_above_reject_threshold(self):
        assert decide_auto_status(31, _settings(30, 70)) == APPLICATION_STATUS_IN_QUEUE

    def test_score_mid_range(self):
        assert decide_auto_status(55, _settings(30, 70)) == APPLICATION_STATUS_IN_QUEUE

    def test_score_one_below_approve_threshold(self):
        assert decide_auto_status(69, _settings(30, 70)) == APPLICATION_STATUS_IN_QUEUE

    def test_score_equal_to_approve_threshold(self):
        assert decide_auto_status(70, _settings(30, 70)) == APPLICATION_STATUS_AUTO_APPROVED

    def test_score_above_approve_threshold(self):
        assert decide_auto_status(100, _settings(30, 70)) == APPLICATION_STATUS_AUTO_APPROVED

    def test_score_zero(self):
        assert decide_auto_status(SCORE_MIN, _settings(30, 70)) == APPLICATION_STATUS_AUTO_REJECTED

    def test_custom_thresholds_honored(self):
        assert decide_auto_status(40, _settings(40, 60)) == APPLICATION_STATUS_AUTO_REJECTED
        assert decide_auto_status(45, _settings(40, 60)) == APPLICATION_STATUS_IN_QUEUE
        assert decide_auto_status(60, _settings(40, 60)) == APPLICATION_STATUS_AUTO_APPROVED


class TestGetThresholdSettings:
    def test_creates_defaults_on_empty_table(self):
        engine, db = _make_db()
        try:
            settings = get_threshold_settings(db)
            assert settings.id == THRESHOLD_SETTINGS_ID
            assert settings.auto_reject_threshold == AUTO_REJECT_THRESHOLD_DEFAULT
            assert settings.auto_approve_threshold == AUTO_APPROVE_THRESHOLD_DEFAULT
            assert db.query(ThresholdSettings).count() == 1
        finally:
            db.close()
            engine.dispose()

    def test_returns_existing_row(self):
        engine, db = _make_db()
        try:
            db.add(ThresholdSettings(
                id=THRESHOLD_SETTINGS_ID,
                auto_reject_threshold=40,
                auto_approve_threshold=60,
            ))
            db.commit()

            settings = get_threshold_settings(db)
            assert settings.auto_reject_threshold == 40
            assert settings.auto_approve_threshold == 60
            assert db.query(ThresholdSettings).count() == 1
        finally:
            db.close()
            engine.dispose()


class TestApplyAutoDecision:
    def test_auto_rejects_low_score(self):
        engine, db = _make_db()
        try:
            application = _make_application(db, score=15)
            status = apply_auto_decision(db, application)
            assert status == APPLICATION_STATUS_AUTO_REJECTED
            assert application.status == APPLICATION_STATUS_AUTO_REJECTED
        finally:
            db.close()
            engine.dispose()

    def test_auto_approves_high_score(self):
        engine, db = _make_db()
        try:
            application = _make_application(db, score=88)
            status = apply_auto_decision(db, application)
            assert status == APPLICATION_STATUS_AUTO_APPROVED
            assert application.status == APPLICATION_STATUS_AUTO_APPROVED
        finally:
            db.close()
            engine.dispose()

    def test_middle_score_stays_in_queue(self):
        engine, db = _make_db()
        try:
            application = _make_application(db, score=55)
            status = apply_auto_decision(db, application)
            assert status == APPLICATION_STATUS_IN_QUEUE
            assert application.status == APPLICATION_STATUS_IN_QUEUE
        finally:
            db.close()
            engine.dispose()

    def test_without_score_keeps_status(self):
        engine, db = _make_db()
        try:
            application = _make_application(db, score=None)
            status = apply_auto_decision(db, application)
            assert status is None
            assert application.status == APPLICATION_STATUS_IN_QUEUE
        finally:
            db.close()
            engine.dispose()

    def test_custom_thresholds_used_from_db(self):
        engine, db = _make_db()
        try:
            db.add(ThresholdSettings(
                id=THRESHOLD_SETTINGS_ID,
                auto_reject_threshold=40,
                auto_approve_threshold=60,
            ))
            db.commit()

            low = _make_application(db, score=20, login="ivan")
            middle = _make_application(db, score=55, login="petr")
            high = _make_application(db, score=65, login="sidor")

            assert apply_auto_decision(db, low) == APPLICATION_STATUS_AUTO_REJECTED
            assert apply_auto_decision(db, middle) == APPLICATION_STATUS_IN_QUEUE
            assert apply_auto_decision(db, high) == APPLICATION_STATUS_AUTO_APPROVED
        finally:
            db.close()
            engine.dispose()