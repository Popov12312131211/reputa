import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from datetime import date

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest
from app.core.constants import PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH


def _mock_db(existing_login=None, fail_commit=False):
    class FakeDb:
        def __init__(self, existing_login):
            self._existing_login = existing_login
            self.added = []
            self.committed = False
            self.refreshed = None
            self.rolled_back = False
            self._fail_commit = fail_commit

        def query(self, model):
            self._query_model = model
            return self

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            if self._existing_login is not None:
                user = User(
                    id=1,
                    full_name="Иван",
                    birth_date=date(1995, 1, 1),
                    login=self._existing_login,
                    password_hash="x",
                    phone="+79990000000",
                    telegram="@ivan",
                    role=UserRole.USER.value,
                )
                return user
            return None

        def add(self, obj):
            self.added.append(obj)

        def commit(self):
            if self._fail_commit:
                raise IntegrityError("INSERT INTO users", {"login": "ivan"}, Exception("UNIQUE"))
            self.committed = True
            for obj in self.added:
                obj.id = 1 if getattr(obj, "id", None) is None else obj.id

        def rollback(self):
            self.rolled_back = True

        def refresh(self, obj):
            self.refreshed = obj

    return FakeDb(existing_login)


def _valid_payload(**overrides):
    data = {
        "full_name": "Иван Петров",
        "birth_date": "1995-05-20",
        "login": "ivan",
        "password": "Abcdef1!",
        "phone": "+79990000000",
        "telegram": "@ivan",
    }
    data.update(overrides)
    return data


class TestRegistrationEndpoint:
    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        self._overrides_cleared = False

    def teardown_method(self):
        app.dependency_overrides.clear()

    def _set_db(self, db):
        app.dependency_overrides[get_db] = lambda: db

    def test_register_success(self):
        db = _mock_db(existing_login=None)
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload())
        assert resp.status_code == 201
        body = resp.json()
        assert body["login"] == "ivan"
        assert body["full_name"] == "Иван Петров"
        assert body["role"] == UserRole.USER.value
        assert body["id"] == 1
        assert db.committed is True
        assert len(db.added) == 1
        assert db.added[0].password_hash != "Abcdef1!"

    def test_register_duplicate_login(self):
        db = _mock_db(existing_login="ivan")
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload())
        assert resp.status_code == 409
        assert db.committed is False

    def test_register_password_too_short(self):
        db = _mock_db(existing_login=None)
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload(password="Ab1!"))
        assert resp.status_code == 422
        assert db.committed is False

    def test_register_password_too_long(self):
        db = _mock_db(existing_login=None)
        self._set_db(db)

        long_pw = "A" + "b" * (PASSWORD_MAX_LENGTH - 1) + "1!"
        resp = self.client.post("/auth/register", json=_valid_payload(password=long_pw))
        assert resp.status_code == 422
        assert db.committed is False

    def test_register_password_no_uppercase(self):
        db = _mock_db(existing_login=None)
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload(password="abcdef1!"))
        assert resp.status_code == 422

    def test_register_password_no_lowercase(self):
        db = _mock_db(existing_login=None)
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload(password="ABCDEF1!"))
        assert resp.status_code == 422

    def test_register_password_no_digit(self):
        db = _mock_db(existing_login=None)
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload(password="Abcdefg!"))
        assert resp.status_code == 422

    def test_register_password_no_special(self):
        db = _mock_db(existing_login=None)
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload(password="Abcdefg1"))
        assert resp.status_code == 422

    def test_register_invalid_phone(self):
        db = _mock_db(existing_login=None)
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload(phone="abc"))
        assert resp.status_code == 422

    def test_register_telegram_no_at(self):
        db = _mock_db(existing_login=None)
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload(telegram="ivan"))
        assert resp.status_code == 422

    def test_register_empty_full_name(self):
        db = _mock_db(existing_login=None)
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload(full_name=""))
        assert resp.status_code == 422

    def test_register_empty_login(self):
        db = _mock_db(existing_login=None)
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload(login=""))
        assert resp.status_code == 422

    def test_register_race_duplicate_returns_409(self):
        db = _mock_db(existing_login=None, fail_commit=True)
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload())
        assert resp.status_code == 409
        assert db.rolled_back is True

    def test_register_future_birth_date(self):
        db = _mock_db(existing_login=None)
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload(birth_date="2050-01-01"))
        assert resp.status_code == 422
        assert db.committed is False

    def test_register_too_old_birth_date(self):
        db = _mock_db(existing_login=None)
        self._set_db(db)

        resp = self.client.post("/auth/register", json=_valid_payload(birth_date="1800-01-01"))
        assert resp.status_code == 422
        assert db.committed is False


class TestPasswordValidation:
    def test_valid_password_accepted(self):
        req = RegisterRequest(
            full_name="Test",
            birth_date=date(2000, 1, 1),
            login="test",
            password="Abcdef1!",
            phone="+79990000000",
            telegram="@test",
        )
        assert req.password == "Abcdef1!"

    def test_min_length_rejected(self):
        pw = "A" * (PASSWORD_MIN_LENGTH - 1) + "1!"
        with pytest.raises(ValidationError):
            RegisterRequest(
                full_name="Test",
                birth_date=date(2000, 1, 1),
                login="test",
                password=pw,
                phone="+79990000000",
                telegram="@test",
            )

    def test_max_length_rejected(self):
        pw = "Aa1!" + "x" * PASSWORD_MAX_LENGTH
        with pytest.raises(ValidationError):
            RegisterRequest(
                full_name="Test",
                birth_date=date(2000, 1, 1),
                login="test",
                password=pw,
                phone="+79990000000",
                telegram="@test",
            )
