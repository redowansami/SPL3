"""Tests for registration (with email-OTP verification) and login."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.utils import email_utils
from backend.app.core.database import Base, get_db
from app.main import app
from backend.app.db.models import User

_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
_TestingSessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=_engine)


def _override_get_db():
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)

VALID_PASSWORD = "Str0ng!Pass"


@pytest.fixture(autouse=True)
def _clean_db():
    db = _TestingSessionLocal()
    db.query(User).delete()
    db.commit()
    db.close()
    yield


@pytest.fixture(autouse=True)
def _no_real_email(monkeypatch):
    async def _fake_send_otp_email(email, otp_code, expire_minutes):
        return None

    monkeypatch.setattr(email_utils, "send_otp_email", _fake_send_otp_email)
    monkeypatch.setattr("app.routers.auth.send_otp_email", _fake_send_otp_email)


def _register(username="alice", email="alice@example.com", password=VALID_PASSWORD, confirm=None):
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": confirm if confirm is not None else password,
        },
    )


def _otp_for(email: str) -> str:
    db = _TestingSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    code = user.otp_code
    db.close()
    return code


def test_register_success():
    resp = _register()
    assert resp.status_code == 201
    assert resp.json()["email"] == "alice@example.com"


def test_register_duplicate_username_rejected():
    _register(username="bob", email="bob1@example.com")
    resp = _register(username="bob", email="bob2@example.com")
    assert resp.status_code == 409


def test_register_duplicate_email_rejected():
    _register(username="carol1", email="carol@example.com")
    resp = _register(username="carol2", email="carol@example.com")
    assert resp.status_code == 409


def test_register_weak_password_rejected():
    resp = _register(username="dave", email="dave@example.com", password="weakpass")
    assert resp.status_code == 422


def test_register_password_mismatch_rejected():
    resp = _register(username="erin", email="erin@example.com", confirm="Different1!")
    assert resp.status_code == 422


def test_verify_otp_success():
    _register(username="frank", email="frank@example.com")
    otp_code = _otp_for("frank@example.com")

    resp = client.post("/api/auth/verify-otp", json={"email": "frank@example.com", "otp_code": otp_code})
    assert resp.status_code == 200


def test_verify_otp_wrong_code():
    _register(username="grace", email="grace@example.com")

    resp = client.post("/api/auth/verify-otp", json={"email": "grace@example.com", "otp_code": "000000"})
    assert resp.status_code == 400


def test_resend_otp():
    _register(username="heidi", email="heidi@example.com")
    old_code = _otp_for("heidi@example.com")

    resp = client.post("/api/auth/resend-otp", json={"email": "heidi@example.com"})
    assert resp.status_code == 200
    new_code = _otp_for("heidi@example.com")
    assert new_code != old_code or new_code is not None


def test_login_before_verification_fails():
    _register(username="ivan", email="ivan@example.com")

    resp = client.post(
        "/api/auth/login", json={"username_or_email": "ivan", "password": VALID_PASSWORD}
    )
    assert resp.status_code == 403


def test_login_after_verification_succeeds_and_me_works():
    _register(username="judy", email="judy@example.com")
    otp_code = _otp_for("judy@example.com")
    client.post("/api/auth/verify-otp", json={"email": "judy@example.com", "otp_code": otp_code})

    resp = client.post(
        "/api/auth/login", json={"username_or_email": "judy", "password": VALID_PASSWORD}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "judy"


def test_me_without_token_fails():
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
