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


def _user(user_id=1):
    return User(
        id=user_id,
        full_name="Иванов Иван Иванович",
        birth_date=date(1995, 5, 20),
        login="ivan",
        password_hash="hash",
        phone="+79990000000",
        telegram="@ivan",
        role=UserRole.USER.value,
    )


class FakeDb:
    def __init__(self, rows):
        self._rows = rows

    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        for arg in args:
            # SQLAlchemy сравнивает колонку с литералом через правую часть
            # выражения (BindParameter), из неё и достаём значение.
            column = getattr(arg, "left", None)
            right = getattr(arg, "right", None)
            value = getattr(right, "value", right)
            self._conds = getattr(self, "_conds", [])
            self._conds.append((getattr(column, "name", None), value))
        return self

    def first(self):
        for row in self._rows:
            if all(getattr(row, name) == value for name, value in self._conds):
                return row
        return None


class ListFakeDb:
    """Fake DB для GET /user/applications (query -> filter -> order_by -> all)."""

    def __init__(self, rows):
        self._rows = rows
        self._conds = []

    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        for arg in args:
            column = getattr(arg, "left", None)
            right = getattr(arg, "right", None)
            value = getattr(right, "value", right)
            self._conds.append((getattr(column, "name", None), value))
        return self

    def order_by(self, *args):
        return self

    def all(self):
        return [r for r in self._rows if all(getattr(r, n) == v for n, v in self._conds)]


class TestUserApplicationList:
    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def _make_application(self, app_id, user_id=1):
        return Application(
            id=app_id,
            user_id=user_id,
            amount=Decimal("1000.00"),
            purpose="Покупка ноутбука",
            telegram="@ivan",
            telegram_channel="@ivan_channel",
            status="in_queue",
            score=None,
            created_at=datetime(2026, 9, 1, 12, 0, 0),
        )

    def test_lists_only_current_users_applications(self):
        # Чужая заявка (user_id=2) должна отсекаться фильтром по текущему пользователю.
        rows = [
            self._make_application(app_id="a1b2c3d4e5f6", user_id=1),
            self._make_application(app_id="b2c3d4e5f607", user_id=2),
        ]
        app.dependency_overrides[get_db] = lambda: ListFakeDb(rows)
        app.dependency_overrides[get_current_user] = lambda: _user(1)
        resp = self.client.get(
            "/user/applications",
            cookies={"access_token": create_access_token(_user(1))},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert [row["id"] for row in body] == ["a1b2c3d4e5f6"]

    def test_unauthenticated_returns_401(self):
        app.dependency_overrides[get_db] = lambda: ListFakeDb([])
        app.dependency_overrides.pop(get_current_user, None)
        resp = self.client.get("/user/applications")
        assert resp.status_code == 401


class TestUserApplicationDetail:
    def setup_method(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def _set_db(self, db):
        app.dependency_overrides[get_db] = lambda: db

    def _set_user(self, user=None):
        app.dependency_overrides[get_current_user] = lambda: user or _user()

    def _make_application(self, user_id=1):
        return Application(
            id="a1b2c3d4e5f6",
            user_id=user_id,
            amount=Decimal("100000.00"),
            purpose="Покупка ноутбука",
            telegram="@ivan",
            telegram_channel="@ivan_channel",
            status="in_queue",
            score=None,
            created_at=datetime(2026, 9, 1, 12, 0, 0),
        )

    def _get(self, application_id="a1b2c3d4e5f6", db=None, user=None):
        if db is not None:
            self._set_db(db)
        self._set_user(user)
        return self.client.get(
            f"/user/applications/{application_id}",
            cookies={"access_token": create_access_token(user or _user())},
        )

    def test_own_application_returns_detail(self):
        db = FakeDb([self._make_application(user_id=1)])
        resp = self._get(db=db, user=_user(1))
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == "a1b2c3d4e5f6"
        assert body["user_id"] == 1
        assert body["full_name"] == "Иванов Иван Иванович"
        assert body["amount"] == "100000.00"
        assert body["purpose"] == "Покупка ноутбука"
        assert body["status"] == "in_queue"
        assert body["score"] is None

    def test_foreign_application_returns_404(self):
        # Чужая заявка (принадлежит другому пользователю) не должна быть доступна.
        db = FakeDb([self._make_application(user_id=2)])
        resp = self._get(db=db, user=_user(1))
        assert resp.status_code == 404

    def test_nonexistent_application_returns_404(self):
        db = FakeDb([self._make_application(user_id=1)])
        resp = self._get(application_id="zzzz999999", db=db, user=_user(1))
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self):
        # Не задаём override get_current_user -> сработает реальная зависимость,
        # которая без cookie вернёт 401 ещё до чтения данных.
        self._set_db(FakeDb([self._make_application(user_id=1)]))
        app.dependency_overrides.pop(get_current_user, None)
        resp = self.client.get("/user/applications/a1b2c3d4e5f6")
        assert resp.status_code == 401
