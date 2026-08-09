from __future__ import annotations

import os
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from starlette.requests import Request

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings
from app.db import engine, init_db
from app.hardening import AuthRateLimiter
from app.main import _save_upload_with_limit, app
from app.models import User
from app.security import hash_password


init_db()
client = TestClient(app)


def test_production_config_accepts_explicit_secret_key() -> None:
    env = os.environ.copy()
    env.update(
        {
            "ENV": "production",
            "SECRET_KEY": "s" * 48,
            "ALLOWED_ORIGINS": "https://app.charleysllc.com",
            "PUBLIC_APP_URL": "https://app.charleysllc.com",
            "MONITORING_SECRET": "m" * 48,
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from app.config import settings; assert settings.secret_key == 's' * 48; assert settings.restricted_environment",
        ],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_upload_name_collision_never_deletes_existing_file(tmp_path: Path) -> None:
    destination = tmp_path / "existing.pdf"
    sentinel = b"existing-customer-evidence"
    destination.write_bytes(sentinel)
    upload = UploadFile(filename="incoming.pdf", file=BytesIO(b"%PDF-1.4\n%%EOF\n"))

    with pytest.raises(FileExistsError):
        _save_upload_with_limit(upload, destination)

    assert destination.exists()
    assert destination.read_bytes() == sentinel


def _request_from_ip(ip: str) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "https",
            "path": "/auth/token",
            "raw_path": b"/auth/token",
            "query_string": b"",
            "headers": [],
            "client": (ip, 12345),
            "server": ("testserver", 443),
        }
    )


def test_auth_rate_limiter_has_bounded_client_memory(monkeypatch) -> None:
    limiter = AuthRateLimiter()
    monkeypatch.setattr(settings, "auth_rate_limit_max_clients", 128)
    monkeypatch.setattr(settings, "auth_rate_limit_attempts", 1000)

    for index in range(200):
        limiter.check(_request_from_ip(f"10.0.{index // 250}.{index % 250}"), "login")

    assert len(limiter._events) <= 128


def test_failed_additional_checkout_preserves_active_entitlement(monkeypatch) -> None:
    import stripe

    email = f"active-{uuid4().hex}@example.com"
    with Session(engine) as session:
        user = User(
            email=email,
            password_hash=hash_password("password1234"),
            billing_plan="starter",
            billing_status="active",
            stripe_customer_id="cus_existing_active",
            stripe_subscription_id="sub_existing_active",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = user.id

    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test_fake")
    monkeypatch.setattr(
        stripe.Webhook,
        "construct_event",
        lambda payload, signature, secret: {
            "type": "checkout.session.async_payment_failed",
            "data": {
                "object": {
                    "metadata": {"user_id": str(user_id), "plan": "setup"},
                    "customer": "cus_failed_extra_checkout",
                }
            },
        },
    )

    response = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "fake"})
    assert response.status_code == 200, response.text

    with Session(engine) as session:
        stored = session.exec(select(User).where(User.email == email)).first()
        assert stored is not None
        assert stored.billing_status == "active"
        assert stored.billing_plan == "starter"
        assert stored.stripe_subscription_id == "sub_existing_active"
