from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from .config import settings


def email_is_configured() -> bool:
    return bool(
        settings.mail_host
        and settings.reminder_from_email
        and settings.mail_user
        and settings.mail_key
    )


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send an email through the configured encrypted SMTP provider.

    Returns False when mail is not fully configured so reminder jobs can be
    safely tested in development without failing the whole request.
    """
    if not email_is_configured():
        return False

    message = EmailMessage()
    message["From"] = settings.reminder_from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    tls_context = ssl.create_default_context()
    smtp_class = smtplib.SMTP_SSL if settings.mail_use_ssl else smtplib.SMTP
    smtp_kwargs = {"host": settings.mail_host, "port": settings.mail_port, "timeout": 20}
    if settings.mail_use_ssl:
        smtp_kwargs["context"] = tls_context

    with smtp_class(**smtp_kwargs) as smtp:
        if settings.mail_use_tls and not settings.mail_use_ssl:
            smtp.starttls(context=tls_context)
        smtp.login(settings.mail_user, settings.mail_key)
        smtp.send_message(message)
    return True
