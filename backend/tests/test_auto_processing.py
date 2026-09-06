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
    ROLE_EMPLOYEE,
    SCORE_MIN,
    SCORE_MAX,
)
from app.models.application import Application
from app.models.employee_thresholds import EmployeeThresholds
from app.models.user import User, UserRole
from app.services.auto_processing import (
    apply_auto_decision,
    decide_auto_status,
    get_employee_thresholds,
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


def _make_user(db, login="employee", role=UserRole.EMPLOYEE.value):
    user = User(
        full_name="Пётр Сотрудников",
        birth_date=date(1990, 1, 1),
        login=login,
        password_hash="hash",
        phone="+79990000000",
        telegram=f"@{login}",
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_application(db, score=None, user_login="ivan"):
    user = _make_user(db, login=user_login, role=UserRole.USER.value)
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
    return EmployeeThresholds(
        user_id=1,
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


class TestGetEmployeeThresholds:
    def test_creates_defaults_on_empty_table(self):
        engine, db = _make_db()
        try:
            employee = _make_user(db)
            settings = get_employee_thresholds(db, employee)
            assert settings.user_id == employee.id
            assert settings.auto_reject_threshold == AUTO_REJECT_THRESHOLD_DEFAULT
            assert settings.auto_approve_threshold == AUTO_APPROVE_THRESHOLD_DEFAULT
            assert db.query(EmployeeThresholds).count() == 1
        finally:
            db.close()
            engine.dispose()

    def test_returns_existing_row(self):
        engine, db = _make_db()
        try:
            employee = _make_user(db)
            db.add(EmployeeThresholds(
                user_id=employee.id,
                auto_reject_threshold=40,
                auto_approve_threshold=60,
            ))
            db.commit()

            settings = get_employee_thresholds(db, employee)
            assert settings.auto_reject_threshold == 40
            assert settings.auto_approve_threshold == 60
            assert db.query(EmployeeThresholds).count() == 1
        finally:
            db.close()
            engine.dispose()


def _make_employee_with_thresholds(db, login, reject, approve):
    employee = _make_user(db, login=login, role=UserRole.EMPLOYEE.value)
    db.add(EmployeeThresholds(
        user_id=employee.id,
        auto_reject_threshold=reject,
        auto_approve_threshold=approve,
    ))
    db.commit()
    return employee


class TestApplyAutoDecision:
    def test_auto_rejects_low_score(self):
        engine, db = _make_db()
        try:
            _make_employee_with_thresholds(db, "emp1", 30, 70)
            application = _make_application(db, score=15)
            status = apply_auto_decision(db, application)
            assert status == APPLICATION_STATUS_AUTO_REJECTED
            assert application.status == APPLICATION_STATUS_AUTO_REJECTED
            assert application.decided_by is not None
        finally:
            db.close()
            engine.dispose()

    def test_auto_approves_high_score(self):
        engine, db = _make_db()
        try:
            _make_employee_with_thresholds(db, "emp1", 30, 70)
            application = _make_application(db, score=88)
            status = apply_auto_decision(db, application)
            assert status == APPLICATION_STATUS_AUTO_APPROVED
            assert application.status == APPLICATION_STATUS_AUTO_APPROVED
            assert application.decided_by is not None
        finally:
            db.close()
            engine.dispose()

    def test_middle_score_stays_in_queue(self):
        engine, db = _make_db()
        try:
            _make_employee_with_thresholds(db, "emp1", 30, 70)
            application = _make_application(db, score=55)
            status = apply_auto_decision(db, application)
            assert status == APPLICATION_STATUS_IN_QUEUE
            assert application.status == APPLICATION_STATUS_IN_QUEUE
            assert application.decided_by is None
        finally:
            db.close()
            engine.dispose()

    def test_without_score_keeps_status(self):
        engine, db = _make_db()
        try:
            _make_employee_with_thresholds(db, "emp1", 30, 70)
            application = _make_application(db, score=None)
            status = apply_auto_decision(db, application)
            assert status is None
            assert application.status == APPLICATION_STATUS_IN_QUEUE
            assert application.decided_by is None
        finally:
            db.close()
            engine.dispose()

    def test_no_employees_stays_in_queue(self):
        engine, db = _make_db()
        try:
            application = _make_application(db, score=15)
            status = apply_auto_decision(db, application)
            assert status == APPLICATION_STATUS_IN_QUEUE
            assert application.status == APPLICATION_STATUS_IN_QUEUE
            assert application.decided_by is None
        finally:
            db.close()
            engine.dispose()

    def test_skips_employee_whose_thresholds_do_not_match(self):
        engine, db = _make_db()
        try:
            # Первый сотрудник не подпадает под персональные пороги средней
            # оценки, второй — подпадает, и сделку закрывает именно он
            # (независимо от случайного порядка перебора — только он матчится).
            app_score = 45
            first = _make_employee_with_thresholds(db, "emp1", 20, 90)
            second = _make_employee_with_thresholds(db, "emp2", 30, 44)

            application = _make_application(db, score=app_score)
            status = apply_auto_decision(db, application)
            assert status == APPLICATION_STATUS_AUTO_APPROVED
            assert application.decided_by == second.id
            assert application.decided_by != first.id
        finally:
            db.close()
            engine.dispose()

    def test_first_matching_employee_wins(self):
        engine, db = _make_db()
        try:
            # Под пороги попадает только один сотрудник — он и фиксируется
            # как решивший, вне зависимости от порядка случайного перебора.
            app_score = 45
            first = _make_employee_with_thresholds(db, "emp1", 30, 44)
            second = _make_employee_with_thresholds(db, "emp2", 10, 90)

            application = _make_application(db, score=app_score)
            status = apply_auto_decision(db, application)
            assert status == APPLICATION_STATUS_AUTO_APPROVED
            assert application.decided_by == first.id
        finally:
            db.close()
            engine.dispose()

    def test_none_matching_stays_in_queue(self):
        engine, db = _make_db()
        try:
            # Персональные пороги обоих сотрудников не покрывают средний балл —
            # заявка остаётся в очереди даже при наличии сотрудников.
            app_score = 45
            _make_employee_with_thresholds(db, "emp1", 20, 90)
            _make_employee_with_thresholds(db, "emp2", 10, 90)

            application = _make_application(db, score=app_score)
            status = apply_auto_decision(db, application)
            assert status == APPLICATION_STATUS_IN_QUEUE
            assert application.decided_by is None
        finally:
            db.close()
            engine.dispose()

    def test_rejects_with_decided_employee_recorded(self):
        engine, db = _make_db()
        try:
            employee = _make_employee_with_thresholds(db, "emp1", 40, 60)
            application = _make_application(db, score=20)
            status = apply_auto_decision(db, application)
            assert status == APPLICATION_STATUS_AUTO_REJECTED
            assert application.decided_by == employee.id
        finally:
            db.close()
            engine.dispose()

    def test_does_not_touch_already_decided_application(self):
        engine, db = _make_db()
        try:
            employee = _make_employee_with_thresholds(db, "emp1", 30, 70)
            application = _make_application(db, score=88)
            application.status = "employee_approved"
            application.decided_by = employee.id
            db.commit()

            status = apply_auto_decision(db, application)
            assert status == "employee_approved"
            assert application.status == "employee_approved"
            assert application.decided_by == employee.id
        finally:
            db.close()
            engine.dispose()

    def test_clears_stale_decided_by_when_no_match(self):
        engine, db = _make_db()
        try:
            employee = _make_employee_with_thresholds(db, "emp1", 20, 90)
            application = _make_application(db, score=45)
            application.decided_by = employee.id
            db.commit()

            status = apply_auto_decision(db, application)
            assert status == APPLICATION_STATUS_IN_QUEUE
            assert application.status == APPLICATION_STATUS_IN_QUEUE
            assert application.decided_by is None
        finally:
            db.close()
            engine.dispose()


class _KeepOrder:
    @staticmethod
    def shuffle(items):
        pass


class _ReverseOrder:
    @staticmethod
    def shuffle(items):
        items.reverse()


class TestApplyAutoDecisionOrder:
    def test_rng_controls_winner_when_two_employees_match(self):
        # Оба сотрудника матчатся (первый — на approve, второй — на reject),
        # побеждает тот, кто оказался первым после shuffle.
        for rng, expected_status, expected_login in (
            (_KeepOrder, APPLICATION_STATUS_AUTO_APPROVED, "emp1"),
            (_ReverseOrder, APPLICATION_STATUS_AUTO_REJECTED, "emp2"),
        ):
            engine, db = _make_db()
            try:
                first = _make_employee_with_thresholds(db, "emp1", 30, 40)
                second = _make_employee_with_thresholds(db, "emp2", 60, 70)
                application = _make_application(db, score=50)
                status = apply_auto_decision(db, application, rng=rng)
                assert status == expected_status
                expected_id = first.id if expected_login == "emp1" else second.id
                assert application.decided_by == expected_id
            finally:
                db.close()
                engine.dispose()