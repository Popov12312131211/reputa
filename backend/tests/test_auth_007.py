import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.auth import create_access_token


class FakeDb:
    def __init__(self, existing_user=None):
        self._user = existing_user

    def get(self, model, pk):
        if self._user is not None and self._user.id == pk:
            return self._user
        return None


def _make_user(user_id=1, role=UserRole.USER.value):
    return User(
        id=user_id,
        full_name="Иванов Иван Иванович",
        birth_date=date(1995, 5, 20),
        login="ivan",
        password_hash="hash",
        phone="+79990000000",
        telegram="@ivan",
        role=role,
    )


def _token(user_id=1, role=UserRole.USER.value):
    return create_access_token(_make_user(user_id=user_id, role=role))


class TestPrivateRoutesMiddleware:
    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        self._clear_overrides()

    def teardown_method(self):
        self._clear_overrides()

    def _clear_overrides(self):
        app.dependency_overrides.clear()

    def test_user_area_without_cookie_returns_401(self):
        resp = self.client.get("/user/settings")
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Не авторизован"

    def test_employee_area_without_cookie_returns_401(self):
        resp = self.client.get("/employee/settings")
        assert resp.status_code == 401

    def test_bare_user_prefix_without_cookie_returns_401(self):
        resp = self.client.get("/user")
        assert resp.status_code == 401

    def test_lookalike_user_prefix_is_not_protected(self):
        resp = self.client.get("/userprofile")
        assert resp.status_code == 404

    def test_invalid_token_returns_401(self):
        resp = self.client.get("/user/settings", cookies={"access_token": "garbage"})
        assert resp.status_code == 401

    def test_user_token_on_employee_area_returns_401(self):
        resp = self.client.get(
            "/employee/settings",
            cookies={"access_token": _token(role=UserRole.USER.value)},
        )
        assert resp.status_code == 401

    def test_employee_token_on_user_area_returns_401(self):
        resp = self.client.get(
            "/user/settings",
            cookies={"access_token": _token(role=UserRole.EMPLOYEE.value)},
        )
        assert resp.status_code == 401

    def test_valid_user_token_passes_middleware(self):
        # Защищённый префикс проходит middleware; маршрута пока нет -> 404, но не 401.
        resp = self.client.get(
            "/user/settings",
            cookies={"access_token": _token(role=UserRole.USER.value)},
        )
        assert resp.status_code == 404

    def test_valid_employee_token_passes_middleware(self):
        # Маршрут EMP-002 (/employee/settings) уже существует и обращается к БД,
        # поэтому для проверки прохождения middleware берём ещё не реализованный
        # частный маршрут сотрудника: ответ 404 (не 401) означает, что middleware
        # пропустил корректный токен сотрудника.
        resp = self.client.get(
            "/employee/newApplication",
            cookies={"access_token": _token(role=UserRole.EMPLOYEE.value)},
        )
        assert resp.status_code == 404

    def test_public_health_unaffected(self):
        resp = self.client.get("/health")
        assert resp.status_code == 200


class TestMeEndpoint:
    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def _set_db(self, db):
        app.dependency_overrides[get_db] = lambda: db

    def test_me_without_cookie_returns_401(self):
        db = FakeDb(existing_user=_make_user())
        self._set_db(db)

        resp = self.client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self):
        db = FakeDb(existing_user=_make_user())
        self._set_db(db)

        resp = self.client.get("/auth/me", cookies={"access_token": "garbage"})
        assert resp.status_code == 401

    def test_me_with_unknown_user_returns_401(self):
        db = FakeDb(existing_user=None)
        self._set_db(db)

        resp = self.client.get(
            "/auth/me",
            cookies={"access_token": _token(user_id=999, role=UserRole.USER.value)},
        )
        assert resp.status_code == 401

    def test_me_with_valid_user_returns_profile(self):
        db = FakeDb(existing_user=_make_user(role=UserRole.EMPLOYEE.value))
        self._set_db(db)

        resp = self.client.get(
            "/auth/me",
            cookies={"access_token": _token(role=UserRole.EMPLOYEE.value)},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == 1
        assert body["full_name"] == "Иванов Иван Иванович"
        assert body["role"] == UserRole.EMPLOYEE.value