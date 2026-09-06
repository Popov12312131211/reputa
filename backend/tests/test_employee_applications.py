import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from datetime import date, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.application import Application
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
            _make_application(app_id=10, user=borrower, score=84),
            _make_application(app_id=11, user=borrower),
        ]
        self._set_db(_FakeDb(rows))
        self.client.cookies.set("access_token", _token())

        resp = self.client.get("/employee/applications")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2
        assert body[0]["id"] == 10
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