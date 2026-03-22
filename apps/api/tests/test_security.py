import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_and_verify():
    hashed = get_password_hash("mypassword")
    assert verify_password("mypassword", hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_decode_access_token_valid():
    token = create_access_token("user-123")
    assert decode_access_token(token) == "user-123"


def test_decode_access_token_rejects_refresh_token():
    refresh_token = create_refresh_token("user-123")
    with pytest.raises(JWTError):
        decode_access_token(refresh_token)


def test_decode_refresh_token_valid():
    token = create_refresh_token("user-456")
    assert decode_refresh_token(token) == "user-456"


def test_decode_refresh_token_rejects_access_token():
    access_token = create_access_token("user-456")
    with pytest.raises(JWTError):
        decode_refresh_token(access_token)


def test_decode_access_token_invalid_string():
    with pytest.raises(JWTError):
        decode_access_token("not.a.valid.jwt")


def test_decode_refresh_token_invalid_string():
    with pytest.raises(JWTError):
        decode_refresh_token("not.a.valid.jwt")
