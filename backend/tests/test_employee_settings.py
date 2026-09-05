import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from datetime import date

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.threshold_settings import ThresholdSettings
from app.models.user import User, UserRole
from app.schemas.threshold import ThresholdSettingsUpdate
from app.services.auth import create_access_token


def _settings(reject=30, approve=70):
    return ThresholdSettings(
        id=1,
        auto_reject_threshold=reject,
        auto_approve_threshold=approve,
    )


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


class _FakeDb:
    def __init__(self, settings=None):
        self._settings = settings
        self.committed = False
        self.refreshed = None

    def get(self, model, pk):
        if model is User:
            return _make_user()
        return None

    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._settings

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed = obj


class TestReadThresholdSettings:
    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def _set_db(self, db):
        app.dependency_overrides[get_db] = lambda: db

    def test_returns_current_thresholds(self):
        db = _FakeDb(settings=_settings(40, 60))
        self._set_db(db)
        self.client.cookies.set("access_token", _token())

        resp = self.client.get("/employee/settings")
        assert resp.status_code == 200
        body = resp.json()
        assert body["auto_reject_threshold"] == 40
        assert body["auto_approve_threshold"] == 60

    def test_employee_only(self):
        db = _FakeDb(settings=_settings())
        self._set_db(db)

        # Пользовательская роль не допускается на /employee/* — 401 от middleware
        # (role-gate реализован в main.py, см. test_auth_007).
        resp = self.client.get(
            "/employee/settings",
            cookies={"access_token": _token(role=UserRole.USER.value)},
        )
        assert resp.status_code == 401

    def test_without_cookie_returns_401(self):
        db = _FakeDb(settings=_settings())
        self._set_db(db)

        resp = self.client.get("/employee/settings")
        assert resp.status_code == 401


class TestUpdateThresholdSettings:
    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def _set_db(self, db):
        app.dependency_overrides[get_db] = lambda: db

    def test_updates_thresholds(self):
        settings = _settings()
        db = _FakeDb(settings=settings)
        self._set_db(db)
        self.client.cookies.set("access_token", _token())

        resp = self.client.put("/employee/settings", json={"auto_reject_threshold": 25, "auto_approve_threshold": 75})
        assert resp.status_code == 200
        body = resp.json()
        assert body["auto_reject_threshold"] == 25
        assert body["auto_approve_threshold"] == 75
        assert settings.auto_reject_threshold == 25
        assert settings.auto_approve_threshold == 75

    def test_employee_only(self):
        db = _FakeDb(settings=_settings())
        self._set_db(db)

        # Пользовательская роль не допускается на /employee/* — 401 от middleware.
        resp = self.client.put(
            "/employee/settings",
            json={"auto_reject_threshold": 25, "auto_approve_threshold": 75},
            cookies={"access_token": _token(role=UserRole.USER.value)},
        )
        assert resp.status_code == 401

    def test_reject_not_less_than_approve_rejected(self):
        db = _FakeDb(settings=_settings())
        self._set_db(db)
        self.client.cookies.set("access_token", _token())

        resp = self.client.put("/employee/settings", json={"auto_reject_threshold": 70, "auto_approve_threshold": 70})
        assert resp.status_code == 422

    def test_threshold_above_max_rejected(self):
        db = _FakeDb(settings=_settings())
        self._set_db(db)
        self.client.cookies.set("access_token", _token())

        resp = self.client.put("/employee/settings", json={"auto_reject_threshold": 30, "auto_approve_threshold": 101})
        assert resp.status_code == 422

    def test_threshold_below_min_rejected(self):
        db = _FakeDb(settings=_settings())
        self._set_db(db)
        self.client.cookies.set("access_token", _token())

        resp = self.client.put("/employee/settings", json={"auto_reject_threshold": -1, "auto_approve_threshold": 70})
        assert resp.status_code == 422

    def test_without_cookie_returns_401(self):
        db = _FakeDb(settings=_settings())
        self._set_db(db)

        resp = self.client.put("/employee/settings", json={"auto_reject_threshold": 25, "auto_approve_threshold": 75})
        assert resp.status_code == 401


class TestThresholdSettingsUpdateValidation:
    def test_valid(self):
        req = ThresholdSettingsUpdate(auto_reject_threshold=30, auto_approve_threshold=70)
        assert req.auto_reject_threshold == 30
        assert req.auto_approve_threshold == 70

    def test_reject_equal_approve_rejected(self):
        with pytest.raises(ValidationError):
            ThresholdSettingsUpdate(auto_reject_threshold=50, auto_approve_threshold=50)

    def test_reject_above_approve_rejected(self):
        with pytest.raises(ValidationError):
            ThresholdSettingsUpdate(auto_reject_threshold=80, auto_approve_threshold=20)

    def test_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            ThresholdSettingsUpdate(auto_reject_threshold=-1, auto_approve_threshold=70)

    def test_above_max_rejected(self):
        with pytest.raises(ValidationError):
            ThresholdSettingsUpdate(auto_reject_threshold=30, auto_approve_threshold=101)

    def test_zero_and_hundred_valid(self):
        req = ThresholdSettingsUpdate(auto_reject_threshold=0, auto_approve_threshold=100)
        assert req.auto_reject_threshold == 0
        assert req.auto_approve_threshold == 100
