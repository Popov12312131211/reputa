import re
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.core.constants import APPLICATION_ID_LENGTH
from app.models.application import Application, generate_application_id
from app.models.user import User, UserRole

# sha256 hexdigest возвращает [0-9a-f]; первые APPLICTION_ID_LENGTH символов — та же маска.
_HEX_RE = re.compile(r"^[0-9a-f]{" + str(APPLICATION_ID_LENGTH) + r"}$")


def test_generate_application_id_length():
    # INFRA-004: ID — строка из 10-12 символов (здесь ровно 12).
    for _ in range(50):
        app_id = generate_application_id()
        assert 10 <= len(app_id) <= 12
        assert len(app_id) == APPLICATION_ID_LENGTH
        assert _HEX_RE.match(app_id)


def test_generate_application_id_uniqueness():
    # Высокая уникальность: sha256(случайный uuid4) — каждый ID случаен.
    ids = {generate_application_id() for _ in range(200)}
    assert len(ids) == 200


def test_generate_application_id_not_sequential():
    # Отсутствие предсказуемой последовательности: соседние ID не идут подряд
    # и не отличаются на константный шаг (как автоинкремент 1, 2, 3...).
    ids = [generate_application_id() for _ in range(10)]
    for i in range(1, len(ids)):
        assert ids[i] != ids[i - 1]
    numeric = [int(hex_id, 16) for hex_id in ids]
    steps = {numeric[i] - numeric[i - 1] for i in range(1, len(numeric))}
    assert steps != {1}


def _make_user_and_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = testing_session()
    user = User(
        full_name="Иван Петров",
        birth_date=date(1995, 5, 20),
        login="ivan",
        password_hash="hash",
        phone="+79990000000",
        telegram="@ivan",
        role=UserRole.USER.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return db, user


def test_application_gets_string_id_on_insert():
    # ID генерируется в default= колонки в момент создания записи — явно
    # id не задаём, после flush он обязан быть строкой нужного формата.
    db, user = _make_user_and_db()
    try:
        app = Application(
            user_id=user.id,
            amount=Decimal("50000.00"),
            purpose="Ремонт квартиры",
            telegram="@ivan",
            telegram_channel="@ivan_channel",
        )
        db.add(app)
        db.commit()
        db.refresh(app)

        assert isinstance(app.id, str)
        assert 10 <= len(app.id) <= 12
        assert _HEX_RE.match(app.id)
    finally:
        db.close()