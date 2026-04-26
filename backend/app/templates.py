from __future__ import annotations

from datetime import date, timedelta

from .models import Task


ASSISTED_LIVING_TASKS: list[tuple[str, str, int]] = [
    (
        "Business license and operating permit",
        "Upload current license, operating permit, and renewal notes. Organizational reminder only; confirm requirements with your regulator.",
        30,
    ),
    (
        "Fire inspection documentation",
        "Upload latest fire inspection report, corrective actions, and next inspection target date.",
        30,
    ),
    (
        "Insurance certificates",
        "Upload general liability, property, workers compensation, and other applicable insurance documents.",
        30,
    ),
    (
        "Staff training records",
        "Upload training logs, certifications, orientation records, and renewal dates.",
        14,
    ),
    (
        "Staff background check records",
        "Track where background check confirmations are stored and when updates are needed.",
        14,
    ),
    (
        "Resident records index",
        "Confirm resident file checklist is current. Do not upload sensitive medical records unless your deployment is configured for that data.",
        14,
    ),
    (
        "Medication log review",
        "Upload or note where medication administration logs are stored and review for missing signatures.",
        7,
    ),
    (
        "Incident report binder",
        "Upload incident report index, follow-up notes, and corrective-action tracking documents.",
        7,
    ),
    (
        "Emergency and evacuation plan",
        "Upload current emergency plan, evacuation map, and staff acknowledgement records.",
        21,
    ),
    (
        "Safety drill records",
        "Upload fire drill, emergency drill, and resident safety documentation.",
        21,
    ),
    (
        "Maintenance and repair log",
        "Track inspection-sensitive maintenance items, open repairs, and completed repair documentation.",
        14,
    ),
    (
        "Policies and procedures",
        "Upload current policy manual, revision notes, and staff acknowledgement records.",
        30,
    ),
]


def default_tasks_for_industry(industry: str, binder_id: int) -> list[Task]:
    normalized = (industry or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in {"assisted_living", "care_home", "small_care_home"}:
        return []

    today = date.today()
    return [
        Task(
            title=title,
            description=description,
            due_date=today + timedelta(days=days_until_due),
            binder_id=binder_id,
        )
        for title, description, days_until_due in ASSISTED_LIVING_TASKS
    ]
