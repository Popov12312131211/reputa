import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from datetime import date, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.application import Application
from app.models.score_result import ScoreResult
from app.models.user import User, UserRole
from app.services.auth import create_access_token


def _make_user(role=UserRole.EMPLOYEE.value):
    return User(
        id=1,
        full_name="Иванов Иван Иванович",
        birth_date=date(1995, 5, 20),
        login="ivan",
        password_hash="hash",
        phone="+79990000000",
        telegram="@ivan",
        role=role,
    )


def _token(role=UserRole.EMPLOYEE.value):
    return create_access_token(_make_user(role=role))


def _make_application(app_id, user, score=None):
    return Application(
        id=app_id,
        user_id=user.id,
        amount=Decimal("1000.00"),
        purpose="Покупка ноутбука",
        telegram="@ivan",
        telegram_channel="@ivan_channel",
        status="in_queue",
        score=score,
        created_at=datetime(2026, 9, 1, 12, 0, 0),
        user=user,
    )


class _FakeDb:
    def __init__(self, rows):
        self._rows = rows

    def query(self, model):
        return self

    def order_by(self, *args):
        return self

    def all(self):
        return list(self._rows)


class TestEmployeeApplicationList:
    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def _set_db(self, db):
        app.dependency_overrides[get_db] = lambda: db

    def test_returns_all_applications_with_full_name(self):
        # Сотрудник видит заявки ВСЕХ заёмщиков, full_name приходит из users.
        app.dependency_overrides[get_current_user] = lambda: _make_user()
        borrower = User(
            id=2,
            full_name="Петрова Анна Сергеевна",
            birth_date=date(1998, 3, 15),
            login="petrova",
            password_hash="hash",
            phone="+79990000001",
            telegram="@petrova",
            role=UserRole.USER.value,
        )
        rows = [
            _make_application(app_id="a1b2c3d4e5f6", user=borrower, score=84),
            _make_application(app_id="b2c3d4e5f607", user=borrower),
        ]
        self._set_db(_FakeDb(rows))
        self.client.cookies.set("access_token", _token())

        resp = self.client.get("/employee/applications")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2
        assert body[0]["id"] == "a1b2c3d4e5f6"
        assert body[0]["full_name"] == "Петрова Анна Сергеевна"
        assert body[0]["amount"] == "1000.00"
        assert body[0]["status"] == "in_queue"
        assert body[0]["score"] == 84
        assert body[1]["score"] is None

    def test_empty_list(self):
        app.dependency_overrides[get_current_user] = lambda: _make_user()
        self._set_db(_FakeDb([]))
        self.client.cookies.set("access_token", _token())

        resp = self.client.get("/employee/applications")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_employee_only(self):
        # Пользовательская роль не допускается на /employee/* — 401 от middleware.
        self._set_db(_FakeDb([]))
        resp = self.client.get(
            "/employee/applications",
            cookies={"access_token": _token(role=UserRole.USER.value)},
        )
        assert resp.status_code == 401

    def test_without_cookie_returns_401(self):
        self._set_db(_FakeDb([]))
        resp = self.client.get("/employee/applications")
        assert resp.status_code == 401


class _FakeDetailDb:
    """Fake DB для GET /employee/applications/{id} (query -> filter -> first)."""

    def __init__(self, rows):
        self._rows = rows

    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._rows[0] if self._rows else None


class TestEmployeeApplicationDetail:
    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def _set_db(self, db):
        app.dependency_overrides[get_db] = lambda: db

    def _set_user(self, user=None):
        app.dependency_overrides[get_current_user] = lambda: user or _make_user()

    def _make_borrower(self):
        return User(
            id=2,
            full_name="Петрова Анна Сергеевна",
            birth_date=date(1998, 3, 15),
            login="petrova",
            password_hash="hash",
            phone="+79990000001",
            telegram="@petrova",
            role=UserRole.USER.value,
        )

    def _make_application(self, app_id, user, score=None, score_result=None):
        app = _make_application(app_id=app_id, user=user, score=score)
        app.score_result = score_result
        return app

    def test_returns_detail_with_score_result(self):
        # EMP-005: карточка сотрудника включает ФИО заёмщика и полный разбор
        # скоринга (сигналы, портрет, отчёт), которого нет у заёмщика.
        borrower = self._make_borrower()
        score_result = ScoreResult(
            application_id="a1b2c3d4e5f6",
            positive_signals=["Регулярные поступления"],
            risk_factors=["Нерегулярный доход"],
            stability_score=8,
            financial_literacy_score=7,
            responsibility_score=9,
            report_content="Отчёт для кредитного комитета по заявке.",
            score=61,
        )
        rows = [self._make_application(app_id="a1b2c3d4e5f6", user=borrower, score=61, score_result=score_result)]
        self._set_db(_FakeDetailDb(rows))
        self._set_user()
        resp = self.client.get(
            "/employee/applications/a1b2c3d4e5f6",
            cookies={"access_token": _token()},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == "a1b2c3d4e5f6"
        assert body["full_name"] == "Петрова Анна Сергеевна"
        assert body["score"] == 61
        assert body["score_result"]["positive_signals"] == ["Регулярные поступления"]
        assert body["score_result"]["risk_factors"] == ["Нерегулярный доход"]
        assert body["score_result"]["stability_score"] == 8
        assert body["score_result"]["financial_literacy_score"] == 7
        assert body["score_result"]["responsibility_score"] == 9
        assert body["score_result"]["report_content"] == "Отчёт для кредитного комитета по заявке."
        assert body["score_result"]["score"] == 61

    def test_returns_detail_without_score_result(self):
        # Пока скоринг не рассчитан (STMT-002/TG-003), score_result приходит null.
        borrower = self._make_borrower()
        rows = [self._make_application(app_id="b2c3d4e5f607", user=borrower, score=None)]
        self._set_db(_FakeDetailDb(rows))
        self._set_user()
        resp = self.client.get(
            "/employee/applications/b2c3d4e5f607",
            cookies={"access_token": _token()},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == "b2c3d4e5f607"
        assert body["score_result"] is None

    def _make_deciding_employee(self):
        return User(
            id=3,
            full_name="Сидоров Пётр Иванович",
            birth_date=date(1990, 1, 10),
            login="sidorov",
            password_hash="hash",
            phone="+79990000003",
            telegram="@sidorov",
            role=UserRole.EMPLOYEE.value,
        )

    def test_returns_decided_by_employee(self):
        # EMP-005: после решения заявки карточка показывает ФИО и логин
        # сотрудника, принявшего решение.
        app = self._make_application(app_id="c3d4e5f6a718", user=self._make_borrower(), score=None)
        app.decided_by_user = self._make_deciding_employee()
        self._set_db(_FakeDetailDb([app]))
        self._set_user()
        resp = self.client.get(
            "/employee/applications/c3d4e5f6a718",
            cookies={"access_token": _token()},
        )
        assert resp.status_code == 200
        assert resp.json()["decided_by_employee"] == {
            "login": "sidorov",
            "full_name": "Сидоров Пётр Иванович",
        }

    def test_decided_by_employee_is_null_before_decision(self):
        # Пока решение не принято (статус in_queue), решивший сотрудник не задан.
        borrower = self._make_borrower()
        rows = [self._make_application(app_id="d4e5f6a7898a", user=borrower, score=None)]
        self._set_db(_FakeDetailDb(rows))
        self._set_user()
        resp = self.client.get(
            "/employee/applications/d4e5f6a7898a",
            cookies={"access_token": _token()},
        )
        assert resp.status_code == 200
        assert resp.json()["decided_by_employee"] is None

    def test_nonexistent_application_returns_404(self):
        self._set_db(_FakeDetailDb([]))
        self._set_user()
        resp = self.client.get(
            "/employee/applications/zzzz999999",
            cookies={"access_token": _token()},
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Заявка не найдена"

    def test_employee_only(self):
        # Пользовательская роль не допускается на /employee/* — 401 от middleware.
        self._set_db(_FakeDetailDb([]))
        resp = self.client.get(
            "/employee/applications/a1b2c3d4e5f6",
            cookies={"access_token": _token(role=UserRole.USER.value)},
        )
        assert resp.status_code == 401

    def test_without_cookie_returns_401(self):
        self._set_db(_FakeDetailDb([]))
        resp = self.client.get("/employee/applications/a1b2c3d4e5f6")
        assert resp.status_code == 401