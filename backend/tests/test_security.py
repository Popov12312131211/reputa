from app.services.security import create_access_token, decode_access_token


def test_create_and_decode_roundtrip():
    token = create_access_token(7)
    assert decode_access_token(token) == 7


def test_decode_garbage_returns_none():
    assert decode_access_token("not-a-jwt") is None


def test_decode_empty_returns_none():
    assert decode_access_token("") is None


def test_decode_tampered_token_returns_none():
    token = create_access_token(7)
    altered = token[:-4] + "aaaa"
    assert decode_access_token(altered) is None