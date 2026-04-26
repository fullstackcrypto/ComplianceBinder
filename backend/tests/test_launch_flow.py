from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db import engine, init_db
from app.main import app
from app.models import User


init_db()
client = TestClient(app)


def auth_headers(email: str | None = None, password: str = "password123") -> tuple[str, dict[str, str]]:
    password = password[:72]
    email = email or f"tester-{uuid4().hex}@example.com"
    client.post("/auth/register", json={"email": email, "password": password})
    response = client.post("/auth/token", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return email, {"Authorization": f"Bearer {token}"}


def activate_paid_access(email: str, plan: str = "starter") -> None:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user is not None
        user.billing_plan = plan
        user.billing_status = "active"
        session.add(user)
        session.commit()


def test_health_endpoint_responds() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"healthy", "degraded"}


def test_assisted_living_binder_seeds_template_tasks() -> None:
    _, headers = auth_headers()
    response = client.post(
        "/binders",
        json={"name": "Sunrise Care Home", "industry": "assisted_living"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    binder_id = response.json()["id"]

    tasks = client.get(f"/binders/{binder_id}/tasks", headers=headers)
    assert tasks.status_code == 200
    titles = [task["title"] for task in tasks.json()]
    assert "Business license and operating permit" in titles
    assert "Medication log review" in titles


def test_report_html_escapes_user_content() -> None:
    _, headers = auth_headers()
    binder = client.post(
        "/binders",
        json={"name": "<script>alert(1)</script>", "industry": "general"},
        headers=headers,
    )
    assert binder.status_code == 201, binder.text
    binder_id = binder.json()["id"]

    report = client.get(f"/binders/{binder_id}/report", headers=headers)
    assert report.status_code == 200
    assert "<script>alert(1)</script>" not in report.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in report.text


def test_pdf_export_requires_paid_status() -> None:
    _, headers = auth_headers()
    binder = client.post("/binders", json={"name": "PDF Gate", "industry": "general"}, headers=headers)
    assert binder.status_code == 201, binder.text

    response = client.get(f"/binders/{binder.json()['id']}/report.pdf", headers=headers)
    assert response.status_code == 402


def test_pdf_export_succeeds_for_paid_user() -> None:
    email, headers = auth_headers()
    binder = client.post("/binders", json={"name": "Paid PDF", "industry": "general"}, headers=headers)
    assert binder.status_code == 201, binder.text
    activate_paid_access(email)

    response = client.get(f"/binders/{binder.json()['id']}/report.pdf", headers=headers)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")


def test_upload_rejects_unsupported_file_type() -> None:
    _, headers = auth_headers()
    binder = client.post("/binders", json={"name": "Upload Gate", "industry": "general"}, headers=headers)
    assert binder.status_code == 201, binder.text
    binder_id = binder.json()["id"]

    response = client.post(
        f"/binders/{binder_id}/documents",
        headers=headers,
        files={"file": ("malware.exe", b"not real", "application/octet-stream")},
        data={"note": "bad"},
    )
    assert response.status_code == 415


def test_oversized_password_is_rejected_cleanly() -> None:
    response = client.post(
        "/auth/register",
        json={"email": f"long-password-{uuid4().hex}@example.com", "password": "x" * 73},
    )
    assert response.status_code == 422


def test_reminder_job_requires_secret() -> None:
    response = client.post("/reminders/run")
    assert response.status_code in {401, 503}


def test_static_legal_pages_exist() -> None:
    for path in ["/privacy.html", "/terms.html"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "InspectionBinder" in response.text
