from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import Session, select

from .config import settings
from .db import get_session
from .mailer import email_is_configured, send_email
from .models import Binder, Task, User

router = APIRouter(prefix="/reminders", tags=["reminders"])


def _authorize_reminder_job(x_cron_secret: str | None) -> None:
    if not settings.reminder_cron_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Reminder job is not configured")
    if x_cron_secret != settings.reminder_cron_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reminder job secret")


@router.post("/run")
def run_reminders(
    session: Session = Depends(get_session),
    x_cron_secret: str | None = Header(default=None, alias="X-Cron-Secret"),
) -> dict:
    """Send reminder emails for overdue and upcoming open tasks.

    Intended for an external cron provider. The job is protected by the
    X-Cron-Secret header so it can be called from services like GitHub Actions,
    cron-job.org, Render Cron Jobs, or Better Stack.
    """
    _authorize_reminder_job(x_cron_secret)

    today = date.today()
    window_end = today + timedelta(days=settings.reminder_window_days)

    tasks = session.exec(
        select(Task)
        .where(Task.status != "done")
        .where(Task.due_date != None)  # noqa: E711
        .where(Task.due_date <= window_end)
        .order_by(Task.due_date.asc())
    ).all()

    sent = 0
    skipped = 0
    failures = 0
    dry_run = not email_is_configured()

    for task in tasks:
        binder = session.get(Binder, task.binder_id)
        if not binder:
            skipped += 1
            continue
        user = session.get(User, binder.owner_id)
        if not user:
            skipped += 1
            continue

        due_label = "overdue" if task.due_date and task.due_date < today else "upcoming"
        subject = f"InspectionBinder reminder: {task.title}"
        body = (
            f"Task: {task.title}\n"
            f"Binder: {binder.name}\n"
            f"Status: {due_label}\n"
            f"Due date: {task.due_date}\n\n"
            "Open InspectionBinder and update the task or upload supporting documentation.\n\n"
            "This is an organizational reminder, not legal or regulatory advice."
        )

        try:
            if not dry_run:
                send_email(user.email, subject, body)
                sent += 1
            else:
                skipped += 1
        except Exception:
            failures += 1

    return {
        "ok": failures == 0,
        "dry_run": dry_run,
        "tasks_found": len(tasks),
        "sent": sent,
        "skipped": skipped,
        "failures": failures,
    }
