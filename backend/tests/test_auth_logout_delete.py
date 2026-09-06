import os

# Движок приложения создаётся при первом импорте app из settings.DATABASE_URL.
# Для сквозного теста то же значение — sqlite в памяти, реальные таблицы
# создаём через StaticPool ниже (общая БД между запросами).
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.main  # noqa: F401  — регистрирует роутеры и middleware
from app.core.constants import STAFF_LOGIN_CODE
from app.db.base import Base
from app.db.session import get_db
from app.models.application import Application
from app.models.user import User


@pytest.fixture()
def client():
    """Настоящая in-memory SQLite-база, общая для middleware и get_current_user.

    Тот же паттерн, что в test_auth_me_e2e: register пишет пользователя,
    login выпускает настоящий JWT в cookie, эндпоинты выхода/удаления читают
    и удаляют этого же пользователя из той же БД.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Включённые foreign_keys повторяют поведение Postgres: каскадное удаление
    # заявок при удалении пользователя выполняется самой БД.
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
        c.dependency_db_session = TestingSession
        yield c

    main.app.dependency_overrides.clear()
    engine.dispose()


USER_PAYLOAD = {
    "full_name": "Иван Петров",
    "birth_date": "1990-01-01",
    "login": "logout_user",
    "password": "Abcdef1!",
    "phone": "+79990000001",
    "telegram": "@logout_user",
}


def _register_and_login(client, payload=None):
    payload = payload or USER_PAYLOAD
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 201
    # Первый зарегистрированный в пустой БД пользователь — сотрудник (bootstrap),
    # поэтому входим через /auth/login/employee. Обычный /login сотруднику
    # запрещён (AUTH-009).
    r = client.post(
        "/auth/login/employee",
        json={"login": payload["login"], "code": STAFF_LOGIN_CODE, "password": payload["password"]},
    )
    assert r.status_code == 200
    assert client.cookies.get("access_token")
    return payload


class TestProfileSettingsEndToEnd:
    """Сквозная проверка API настроек (APP-006B) на реальной БД, сквозь
    регистрацию/логин/cookie, а не на моках: GET и PATCH /auth/profile."""

    def test_profile_read_update_roundtrip(self, client):
        _register_and_login(client)

        # GET /auth/profile возвращает реальные данные, записанные при регистрации.
        r = client.get("/auth/profile")
        assert r.status_code == 200
        body = r.json()
        assert body["full_name"] == USER_PAYLOAD["full_name"]
        assert body["login"] == USER_PAYLOAD["login"]
        assert body["phone"] == USER_PAYLOAD["phone"]
        assert body["telegram"] == USER_PAYLOAD["telegram"]

        # PATCH: меняем ФИО/логин/телефон/телеграм и пароль.
        r = client.patch(
            "/auth/profile",
            json={
                "full_name": "Пётр Сидоров",
                "login": "updated_login",
                "phone": "+79990000002",
                "telegram": "@updated_tg",
                "password": "NewPass2!",
            },
        )
        assert r.status_code == 200
        updated = r.json()
        assert updated["full_name"] == "Пётр Сидоров"
        assert updated["login"] == "updated_login"
        assert updated["phone"] == "+79990000002"
        assert updated["telegram"] == "@updated_tg"

        # Изменения реально сохранены: GET возвращает их, а вход работает уже
        # по новому логину/паролю.
        r = client.get("/auth/profile")
        assert r.status_code == 200
        assert r.json()["login"] == "updated_login"

        client.post("/auth/logout")
        r = client.post(
            "/auth/login/employee",
            json={"login": "updated_login", "code": STAFF_LOGIN_CODE, "password": "NewPass2!"},
        )
        assert r.status_code == 200

    def test_profile_password_optional(self, client):
        _register_and_login(client)

        # Без поля password профиль обновляется, пароль остаётся прежним.
        r = client.patch(
            "/auth/profile",
            json={
                "full_name": "Иван Иванов",
                "login": "logout_user",
                "phone": "+79990000001",
                "telegram": "@logout_user",
            },
        )
        assert r.status_code == 200

        client.post("/auth/logout")
        r = client.post(
            "/auth/login/employee",
            json={"login": "logout_user", "code": STAFF_LOGIN_CODE, "password": USER_PAYLOAD["password"]},
        )
        assert r.status_code == 200


class TestLogout:
    def test_logout_requires_auth(self, client):
        r = client.post("/auth/logout")
        assert r.status_code == 401
        assert r.json()["detail"] == "Не авторизован"

    def test_logout_clears_cookie(self, client):
        _register_and_login(client)

        r = client.post("/auth/logout")
        assert r.status_code == 204
        # Кука помечается на удаление: Set-Cookie с пустым значением и max-age=0.
        set_cookie = r.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie
        assert "Max-Age=0" in set_cookie or "max-age=0" in set_cookie

        # Cookie из jar исчез — пользователь разлогинен.
        assert not client.cookies.get("access_token")
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_logout_does_not_delete_user(self, client):
        _register_and_login(client)

        client.post("/auth/logout")

        # Пользователь остаётся в БД: повторный вход возможен.
        r = client.post(
            "/auth/login/employee",
            json={"login": "logout_user", "code": STAFF_LOGIN_CODE, "password": "Abcdef1!"},
        )
        assert r.status_code == 200


class TestDeleteAccount:
    def test_delete_requires_auth(self, client):
        r = client.delete("/auth/delete")
        assert r.status_code == 401

    def test_delete_removes_user_and_clears_cookie(self, client):
        _register_and_login(client)

        r = client.delete("/auth/delete")
        assert r.status_code == 204
        assert not client.cookies.get("access_token")

        # Аккаунт реально удалён: вход с прежними данными больше не работает.
        r = client.post("/auth/login", json={"login": "logout_user", "password": "Abcdef1!"})
        assert r.status_code == 401

    def test_delete_cascades_user_applications(self, client):
        payload = _register_and_login(client)

        # Создаём заявку напрямую в той же БД, что использует приложение.
        session = client.dependency_db_session()
        user = session.query(User).filter(User.login == payload["login"]).first()
        session.add(
            Application(
                user_id=user.id,
                amount=Decimal("5000.00"),
                purpose="На корм для уток",
                telegram="@logout_user",
                telegram_channel="@channel",
                status="in_queue",
            )
        )
        session.commit()
        session.close()

        r = client.delete("/auth/delete")
        assert r.status_code == 204

        # Пользователь удалён, а его заявки каскадно удалены: в БД пусто.
        session2 = client.dependency_db_session()
        assert session2.query(User).count() == 0
        assert session2.query(Application).count() == 0
        session2.close()