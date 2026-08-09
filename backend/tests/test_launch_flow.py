from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.config import settings
from app.db import engine, init_db
from app.main import app
from app.models import User


init_db()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
client = TestClient(app)


def auth_headers(email: str | None = None, password: str = "password1234") -> tuple[str, dict[str, str]]:
    password = password[:72]
    email = email or f"tester-{uuid4().hex}@example.com"
    register = client.post("/auth/register", json={"email": email, "password": password})
    assert register.status_code == 201, register.text
    response = client.post("/auth/token", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    return email, {"Authorization": f"Bearer {response.json()['access_token']}"}


def activate_paid_access(email: str, plan: str = "starter") -> None:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user is not None
        user.billing_plan = plan
        user.billing_status = "active"
        session.add(user)
        session.commit()


def user_billing_status(email: str) -> str:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user is not None
        return user.billing_status


def test_health_endpoint_is_minimal() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"healthy", "degraded"}
    assert "database_status" not in body
    assert "storage_status" not in body
    assert "storage_path" not in body


def test_security_headers_are_set() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["referrer-policy"] == "no-referrer"


def test_detailed_monitoring_requires_secret(monkeypatch) -> None:
    monkeypatch.setattr(settings, "monitoring_secret", "m" * 40)
    assert client.get("/metrics").status_code == 401
    assert client.get("/status").status_code == 401
    headers = {"X-Monitoring-Secret": "m" * 40}
    assert client.get("/metrics", headers=headers).status_code == 200
    assert client.get("/status", headers=headers).status_code == 200


def test_assisted_living_binder_seeds_template_tasks() -> None:
    _, headers = auth_headers()
    response = client.post("/binders", json={"name": "Sunrise Care Home", "industry": "assisted_living"}, headers=headers)
    assert response.status_code == 201, response.text
    binder_id = response.json()["id"]
    tasks = client.get(f"/binders/{binder_id}/tasks", headers=headers)
    assert tasks.status_code == 200
    titles = [task["title"] for task in tasks.json()]
    assert len(titles) >= 16
    assert "[ADMIN] Facility license and scope review" in titles
    assert "[OPERATIONS] Medication/documentation readiness location check" in titles
    assert "[REPORT] Final rule-reference and evidence QA" in titles


def test_cross_user_binder_access_is_hidden() -> None:
    _, owner_headers = auth_headers()
    _, outsider_headers = auth_headers()
    binder = client.post("/binders", json={"name": "Private Facility", "industry": "assisted_living"}, headers=owner_headers)
    assert binder.status_code == 201
    binder_id = binder.json()["id"]
    assert client.get(f"/binders/{binder_id}/tasks", headers=outsider_headers).status_code == 404
    assert client.get(f"/binders/{binder_id}/documents", headers=outsider_headers).status_code == 404
    assert client.get(f"/binders/{binder_id}/report", headers=outsider_headers).status_code == 404


def test_report_html_escapes_user_content() -> None:
    _, headers = auth_headers()
    binder = client.post("/binders", json={"name": "<script>alert(1)</script>", "industry": "general"}, headers=headers)
    assert binder.status_code == 201, binder.text
    binder_id = binder.json()["id"]
    report = client.get(f"/binders/{binder_id}/report", headers=headers)
    assert report.status_code == 200
    assert "<script>alert(1)</script>" not in report.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in report.text
    assert report.headers["cache-control"] == "no-store"


def test_pdf_export_requires_paid_status() -> None:
    _, headers = auth_headers()
    binder = client.post("/binders", json={"name": "PDF Gate", "industry": "general"}, headers=headers)
    assert binder.status_code == 201, binder.text
    assert client.get(f"/binders/{binder.json()['id']}/report.pdf", headers=headers).status_code == 402


def test_pdf_export_succeeds_for_paid_user() -> None:
    email, headers = auth_headers()
    binder = client.post("/binders", json={"name": "Paid PDF", "industry": "general"}, headers=headers)
    assert binder.status_code == 201, binder.text
    activate_paid_access(email)
    response = client.get(f"/binders/{binder.json()['id']}/report.pdf", headers=headers)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")
    assert response.headers["cache-control"] == "no-store"


def test_upload_rejects_unsupported_file_type() -> None:
    _, headers = auth_headers()
    binder = client.post("/binders", json={"name": "Upload Gate", "industry": "general"}, headers=headers)
    response = client.post(f"/binders/{binder.json()['id']}/documents", headers=headers, files={"file": ("malware.exe", b"not real", "application/octet-stream")}, data={"note": "bad"})
    assert response.status_code == 415


def test_upload_rejects_spoofed_pdf_content() -> None:
    _, headers = auth_headers()
    binder = client.post("/binders", json={"name": "Spoof Gate", "industry": "general"}, headers=headers)
    response = client.post(f"/binders/{binder.json()['id']}/documents", headers=headers, files={"file": ("fake.pdf", b"MZ-not-a-pdf", "application/pdf")}, data={"note": "spoof"})
    assert response.status_code == 415


def test_document_download_is_owner_only() -> None:
    _, owner_headers = auth_headers()
    _, outsider_headers = auth_headers()
    binder = client.post("/binders", json={"name": "Document Owner", "industry": "general"}, headers=owner_headers)
    upload = client.post(f"/binders/{binder.json()['id']}/documents", headers=owner_headers, files={"file": ("evidence.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")}, data={"note": "evidence"})
    assert upload.status_code == 201, upload.text
    doc_id = upload.json()["id"]
    assert client.get(f"/documents/{doc_id}/download", headers=outsider_headers).status_code == 404
    owner_download = client.get(f"/documents/{doc_id}/download", headers=owner_headers)
    assert owner_download.status_code == 200
    assert owner_download.content.startswith(b"%PDF-")


def test_short_and_oversized_passwords_are_rejected() -> None:
    short = client.post("/auth/register", json={"email": f"short-{uuid4().hex}@example.com", "password": "shortpass"})
    assert short.status_code == 422
    oversized = client.post("/auth/register", json={"email": f"long-{uuid4().hex}@example.com", "password": "x" * 73})
    assert oversized.status_code == 422


def test_input_lengths_are_bounded() -> None:
    _, headers = auth_headers()
    response = client.post("/binders", json={"name": "x" * 161, "industry": "general"}, headers=headers)
    assert response.status_code == 422


def test_billing_status_does_not_expose_stripe_identifiers() -> None:
    _, headers = auth_headers()
    response = client.get("/billing/status", headers=headers)
    assert response.status_code == 200
    assert set(response.json()) == {"plan", "status"}


def test_unpaid_checkout_completion_does_not_grant_access(monkeypatch) -> None:
    import stripe
    email, _ = auth_headers()
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user is not None
        user_id = user.id
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test_fake")
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda payload, signature, secret: {"type": "checkout.session.completed", "data": {"object": {"payment_status": "unpaid", "metadata": {"user_id": str(user_id), "plan": "setup"}, "customer": "cus_fake"}}})
    response = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "fake"})
    assert response.status_code == 200
    assert user_billing_status(email) == "inactive"


def test_paid_checkout_completion_grants_access(monkeypatch) -> None:
    import stripe
    email, _ = auth_headers()
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user is not None
        user_id = user.id
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test_fake")
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda payload, signature, secret: {"type": "checkout.session.completed", "data": {"object": {"payment_status": "paid", "metadata": {"user_id": str(user_id), "plan": "setup"}, "customer": "cus_fake_paid"}}})
    response = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "fake"})
    assert response.status_code == 200
    assert user_billing_status(email) == "active"


def test_reminder_job_requires_secret() -> None:
    response = client.post("/reminders/run")
    assert response.status_code in {401, 503}


def test_static_legal_pages_exist() -> None:
    for path in ["/privacy.html", "/terms.html"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "Ready Set Solutions" in response.text


def test_home_page_exposes_ready_set_pilot() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Ready Set Solutions" in response.text
    assert "Ready Set Pilot" in response.text


def test_frontend_uses_session_scoped_auth_storage() -> None:
    app_js = (BACKEND_ROOT / "app" / "static" / "app.js").read_text(encoding="utf-8")
    assert "localStorage" not in app_js
    assert "sessionStorage" in app_js
