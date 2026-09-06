import os

# Движок приложения создаётся при первом импорте app из settings.DATABASE_URL.
# Для сквозного теста to же значение — sqlite в памяти, реальные таблицы
# создаём через StaticPool ниже (общая БД между запросами).
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.main  # noqa: F401  — регистрирует роутеры и middleware
from app.db.base import Base
from app.db.session import get_db
from app.models.user import UserRole


@pytest.fixture()
def client():
    """Настоящая in-memory SQLite-база, общая для middleware и get_current_user.

    get_db переопределяется на реальную сессию той же БД (не мокая
    get_current_user): register пишет пользователя, login выпускает настоящий
    JWT-токен в cookie, middleware и get_current_user читают этого же
    пользователя из той же таблицы.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    import app.main as main
    main.app.dependency_overrides[get_db] = override_get_db

    with TestClient(app.main.app, raise_server_exceptions=False) as c:
        yield c

    main.app.dependency_overrides.clear()
    engine.dispose()


DUMMY_EMPLOYEE = {
    "full_name": "Иван Петров",
    "birth_date": "1990-01-01",
    "login": "e2e_employee",
    "password": "Abcdef1!",
    "phone": "+79990000003",
    "telegram": "@e2e_employee",
}


class TestAuthMeEndToEnd:
    """Полный сквозной путь через реальную БД: register -> login -> /auth/me.

    Покрывает именно тот пробел, из-за которого ImportError в app.api.deps
    оставался незамеченным до реального запуска контейнера: cookie, который
    ставит login, реально читается middleware и get_current_user на следующих
    запросах.
    """

    def test_employee_login_session_flow(self, client):
        # Первый зарегистрированный пользователь в пустой БД становится employee.
        r = client.post("/auth/register", json=DUMMY_EMPLOYEE)
        assert r.status_code == 201
        assert r.json()["role"] == UserRole.EMPLOYEE.value

        # Логин реально ставит httpOnly-cookie.
        r = client.post("/auth/login", json={"login": "e2e_employee", "password": "Abcdef1!"})
        assert r.status_code == 200
        set_cookie = r.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie
        assert "HttpOnly" in set_cookie
        # TestClient сохраняет cookie jar, как браузер.
        assert client.cookies.get("access_token")

        # /auth/me с тем самым cookie (который поставил login) — 200.
        # MeResponse не содержит login (id/full_name/role), проверяем по роли.
        r = client.get("/auth/me")
        assert r.status_code == 200
        body = r.json()
        assert body["role"] == UserRole.EMPLOYEE.value
        assert body["id"] > 0
        assert body["full_name"]

    def test_register_login_me_user_area(self, client):
        # Первый пользователь — employee (bootstrap). Второй — обычный user.
        # Это нужно, чтобы проверить защищённый префикс /user/* именно для user.
        client.post("/auth/register", json=DUMMY_EMPLOYEE)
        user_payload = {
            "full_name": "Анна Смирнова",
            "birth_date": "1991-02-02",
            "login": "e2e_user",
            "password": "Abcdef2!",
            "phone": "+79990000004",
            "telegram": "@e2e_user",
        }
        r = client.post("/auth/register", json=user_payload)
        assert r.status_code == 201
        assert r.json()["role"] == UserRole.USER.value

        r = client.post("/auth/login", json={"login": "e2e_user", "password": "Abcdef2!"})
        assert r.status_code == 200
        assert client.cookies.get("access_token")

        # Cookie user-роли проходит middleware и /auth/me.
        r = client.get("/auth/me")
        assert r.status_code == 200
        assert r.json()["role"] == UserRole.USER.value

        # Защищённый /user/* для user: 200 (минуя моки, через middleware + get_current_user).
        r = client.get("/user/applications")
        assert r.status_code == 200

    def test_protected_route_requires_cookie(self, client):
        # Без cookie middleware защищает /user/* -> 401.
        r = client.get("/user/applications")
        assert r.status_code == 401
        assert r.json()["detail"] == "Не авторизован"