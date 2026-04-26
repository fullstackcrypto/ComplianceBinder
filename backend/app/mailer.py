from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .config import settings


def email_is_configured() -> bool:
    return bool(settings.mail_host and settings.reminder_from_email)


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send an email through the configured SMTP-compatible provider.

    Returns False when mail is not configured so reminder jobs can be safely
    tested in development without failing the whole request.
    """
    if not email_is_configured():
        return False

    message = EmailMessage()
    message["From"] = settings.reminder_from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.mail_host, settings.mail_port, timeout=20) as smtp:
        if settings.mail_use_tls:
            smtp.starttls()
        if settings.mail_user and settings.mail_key:
            smtp.login(settings.mail_user, settings.mail_key)
        smtp.send_message(message)
    return True
