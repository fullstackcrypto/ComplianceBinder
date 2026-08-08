from __future__ import annotations

from datetime import date, timedelta

from .models import Task


# Launch checklist for the Ready Set Solutions Arizona assisted-living pilot.
# These items are inspection-readiness prompts, not legal conclusions. Final
# customer reports must verify the current applicable rule/statute citation.
ASSISTED_LIVING_TASKS: list[tuple[str, str, int]] = [
    (
        "[ADMIN] Facility license and scope review",
        "Confirm the current facility license, capacity, service level, ownership/contact information, and renewal status. Evidence: current license and renewal records. Regulatory reference family: Arizona DHS licensing requirements / 9 A.A.C. 10. Verify the current applicable subsection before final reporting.",
        7,
    ),
    (
        "[ADMIN] Certified assisted living facility manager",
        "Confirm the facility is operating under the supervision of an appropriately certified assisted living facility manager and retain authorized verification. Reference: A.R.S. § 36-446.01(B). Do not represent Ready Set personnel as the facility manager unless separately qualified and engaged in that role.",
        7,
    ),
    (
        "[PEOPLE] Staff credentials, training and renewals",
        "Review the facility's credential/training index for missing, expired, or soon-due items. Evidence: authorized certificates, training logs, orientation/competency records and renewal dates. Regulatory reference family: current Arizona assisted-living staffing/training requirements; verify the current applicable rule before final reporting.",
        14,
    ),
    (
        "[PEOPLE] Background and personnel-file readiness",
        "Confirm required personnel-file and background-check evidence is organized and retrievable. Record missing/expired evidence as an action item. Avoid uploading sensitive personal information that is not necessary for the readiness report.",
        14,
    ),
    (
        "[SAFETY] Emergency, evacuation and disaster readiness",
        "Verify the current emergency/evacuation plan, evacuation maps, staff acknowledgements, emergency contacts and related readiness evidence are organized. Regulatory reference family: 9 A.A.C. 10 assisted-living requirements; verify the current applicable subsection before final reporting.",
        14,
    ),
    (
        "[SAFETY] Drill and inspection records",
        "Review available fire/emergency drill records, fire/life-safety inspection records, corrective actions and next due dates. Evidence should show what was found, who corrected it and when correction was verified.",
        14,
    ),
    (
        "[PHYSICAL] Exterior, access and egress walkthrough",
        "Walk the exterior, entrances, exits and egress paths. Document observable damage, blocked paths, trip/fall risks, lighting issues, door/lock concerns and other inspection-readiness conditions. Use photos only when privacy-safe. LiDAR is optional screening evidence; verify legally material dimensions with an approved measurement procedure.",
        7,
    ),
    (
        "[PHYSICAL] Common-area safety walkthrough",
        "Inspect common areas for observable maintenance, sanitation, access, furnishing, trip/fall, electrical, lighting and life-safety concerns. For every finding record: location, condition, evidence, priority, action owner and due date.",
        7,
    ),
    (
        "[PHYSICAL] Resident-room environmental walkthrough",
        "Inspect rooms only within the authorized scope. Record facility/environment conditions without photographing residents, medication information or resident-identifying documents. Flag measurement questions for verified measurement rather than automatic pass/fail.",
        7,
    ),
    (
        "[PHYSICAL] Bathroom and bathing-area walkthrough",
        "Review observable safety, maintenance, accessibility, fixture, hot-water/scald-risk, grab/support and sanitation conditions within the agreed scope. Record evidence and corrective actions; verify any threshold-dependent measurement before final reporting.",
        7,
    ),
    (
        "[OPERATIONS] Maintenance and repair action log",
        "Create one list of open inspection-sensitive maintenance items. Each item should have location, issue, evidence, priority, responsible person, due date, completion evidence and verification status.",
        7,
    ),
    (
        "[OPERATIONS] Medication/documentation readiness location check",
        "Confirm the facility can quickly produce its required medication and resident-care documentation during an official survey. Initial Ready Set pilots should not intentionally store resident clinical records/PHI in this application; record where authorized source records are maintained instead.",
        7,
    ),
    (
        "[OPERATIONS] Incident and corrective-action tracking",
        "Confirm incident documentation, follow-up responsibilities and corrective-action evidence can be located when requested. Store only information authorized for the Ready Set data scope; use de-identified indexes whenever possible during the pilot phase.",
        7,
    ),
    (
        "[OPERATIONS] Policies and procedures readiness",
        "Confirm current policies, revision dates and staff acknowledgement evidence are organized and retrievable. Flag policies that appear missing, obsolete or inconsistent for management/legal review rather than declaring a legal violation.",
        21,
    ),
    (
        "[REPORT] Resolve red/high-priority findings",
        "Before issuing the final readiness report, confirm every high-priority finding has a documented owner and corrective-action plan. A Ready Set report is an independent readiness assessment, not an ADHS inspection, certification, legal opinion or guarantee of compliance.",
        3,
    ),
    (
        "[REPORT] Final rule-reference and evidence QA",
        "Quality-review the report before delivery. Verify each cited rule/statute against the current official source, confirm evidence matches the finding, remove unnecessary sensitive information, and ensure the disclaimer is present. Critical citation errors are a stop-ship condition.",
        3,
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
