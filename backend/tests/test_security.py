from datetime import date

from app.models.user import User, UserRole
from app.services.auth import create_access_token, decode_access_token


def _user(user_id=7, role=UserRole.USER.value):
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


def _sub(token):
    return int(decode_access_token(token)["sub"])


def test_create_and_decode_roundtrip():
    token = create_access_token(_user())
    assert _sub(token) == 7


def test_token_keeps_role():
    token = create_access_token(_user(role=UserRole.EMPLOYEE.value))
    assert decode_access_token(token)["role"] == UserRole.EMPLOYEE.value


def test_decode_garbage_returns_none():
    assert decode_access_token("not-a-jwt") is None


def test_decode_empty_returns_none():
    assert decode_access_token("") is None


def test_decode_tampered_token_returns_none():
    token = create_access_token(_user())
    altered = token[:-4] + "aaaa"
    assert decode_access_token(altered) is None