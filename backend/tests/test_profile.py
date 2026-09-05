import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user
from app.core.constants import ROLE_USER
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.services.auth import verify_password


def _user():
    return User(
        id=1,
        full_name="Иван Петров",
        birth_date=date(1995, 5, 20),
        login="ivan",
        password_hash="old-hash",
        phone="+79990000000",
        telegram="@ivan",
        role=ROLE_USER,
    )


class FakeDb:
    def __init__(self, duplicate=False, fail_commit=False):
        self.duplicate = duplicate
        self.fail_commit = fail_commit
        self.committed = False
        self.rolled_back = False

    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return _user() if self.duplicate else None

    def commit(self):
        if self.fail_commit:
            raise IntegrityError("UPDATE users", {}, Exception("UNIQUE"))
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, obj):
        return obj


class TestProfileEndpoint:
    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        self.user = _user()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def _set_dependencies(self, db):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: self.user

    def test_get_profile(self):
        self._set_dependencies(FakeDb())

        response = self.client.get("/auth/profile")

        assert response.status_code == 200
        assert response.json()["login"] == "ivan"
        assert response.json()["role"] == ROLE_USER

    def test_update_profile_and_password(self):
        db = FakeDb()
        self._set_dependencies(db)

        response = self.client.patch(
            "/auth/profile",
            json={
                "full_name": "Петр Иванов",
                "login": "petr",
                "phone": "+79991112233",
                "telegram": "@petr",
                "password": "NewPassword1!",
            },
        )

        assert response.status_code == 200
        assert self.user.login == "petr"
        assert self.user.full_name == "Петр Иванов"
        assert verify_password("NewPassword1!", self.user.password_hash)
        assert db.committed is True

    def test_update_profile_rejects_duplicate_login(self):
        db = FakeDb(duplicate=True)
        self._set_dependencies(db)

        response = self.client.patch(
            "/auth/profile",
            json={
                "full_name": "Петр Иванов",
                "login": "petr",
                "phone": "+79991112233",
                "telegram": "@petr",
            },
        )

        assert response.status_code == 409
        assert db.committed is False

    def test_update_profile_rejects_weak_password(self):
        db = FakeDb()
        self._set_dependencies(db)

        response = self.client.patch(
            "/auth/profile",
            json={
                "full_name": "Петр Иванов",
                "login": "petr",
                "phone": "+79991112233",
                "telegram": "@petr",
                "password": "weak",
            },
        )

        assert response.status_code == 422
        assert db.committed is False