from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.mailer import email_is_configured, send_email


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent


def test_render_blueprint_is_production_ready() -> None:
    blueprint = (REPO_ROOT / "render.yaml").read_text(encoding="utf-8")
    required_fragments = [
        "name: ready-set-compliancebinder",
        "ENV\n        value: production",
        "autoDeployTrigger: checksPass",
        "app.charleysllc.com",
        "mountPath: /var/data",
        "generateValue: true",
        "type: cron",
        'schedule: "0 16 * * *"',
        "python scripts/run_reminder_cron.py",
        "plan: basic-256mb",
        'postgresMajorVersion: "18"',
        "storageAutoscalingEnabled: true",
        "ipAllowList: []",
    ]
    for fragment in required_fragments:
        assert fragment in blueprint
    assert "inspectionbinder-staging" not in blueprint
    assert "requirements-dev.txt" not in blueprint


def test_current_stable_stripe_sdk_is_pinned() -> None:
    requirements = (BACKEND_ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "stripe==15.3.1" in requirements
    assert "stripe==8.6.0" not in requirements


def test_email_configuration_requires_authenticated_credentials(monkeypatch) -> None:
    monkeypatch.setattr(settings, "mail_host", "mail.privateemail.com")
    monkeypatch.setattr(settings, "reminder_from_email", "Ready Set Solutions <support@charleysllc.com>")
    monkeypatch.setattr(settings, "mail_user", "")
    monkeypatch.setattr(settings, "mail_key", "")
    assert email_is_configured() is False

    monkeypatch.setattr(settings, "mail_user", "support@charleysllc.com")
    monkeypatch.setattr(settings, "mail_key", "application-password")
    assert email_is_configured() is True


def test_mailer_uses_starttls_and_authentication(monkeypatch) -> None:
    calls: list[object] = []

    class FakeSMTP:
        def __init__(self, **kwargs):
            calls.append(("init", kwargs))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self, context=None):
            calls.append(("starttls", context is not None))

        def login(self, username, password):
            calls.append(("login", username, password))

        def send_message(self, message):
            calls.append(("send", message["To"]))

    monkeypatch.setattr("app.mailer.smtplib.SMTP", FakeSMTP)
    monkeypatch.setattr(settings, "mail_host", "mail.privateemail.com")
    monkeypatch.setattr(settings, "mail_port", 587)
    monkeypatch.setattr(settings, "mail_user", "support@charleysllc.com")
    monkeypatch.setattr(settings, "mail_key", "application-password")
    monkeypatch.setattr(settings, "reminder_from_email", "Ready Set Solutions <support@charleysllc.com>")
    monkeypatch.setattr(settings, "mail_use_tls", True)
    monkeypatch.setattr(settings, "mail_use_ssl", False)

    assert send_email("customer@example.com", "Subject", "Body") is True
    assert any(item[0] == "starttls" for item in calls)
    assert ("login", "support@charleysllc.com", "application-password") in calls
    assert ("send", "customer@example.com") in calls


def test_reminder_cron_is_https_only_and_does_not_print_secret() -> None:
    cron = (BACKEND_ROOT / "scripts" / "run_reminder_cron.py").read_text(encoding="utf-8")
    assert 'parsed.scheme != "https"' in cron
    assert '"X-Cron-Secret": secret' in cron
    assert "print(secret" not in cron
    assert "repr(secret" not in cron
