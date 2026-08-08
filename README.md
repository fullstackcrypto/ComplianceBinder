[![CI](https://github.com/fullstackcrypto/ComplianceBinder/actions/workflows/ci.yml/badge.svg)](https://github.com/fullstackcrypto/ComplianceBinder/actions/workflows/ci.yml)

# Ready Set Solutions — ComplianceBinder

Ready Set Solutions is an inspection-readiness platform for small regulated operators. The first commercial wedge is **Arizona assisted-living homes and small care facilities**.

The product combines a digital readiness binder, recurring task/reminder workflow, evidence uploads, printable reports, Stripe billing, and a done-with-you service model that can be delivered by trained Ready Set field specialists.

## Commercial launch offer

### Ready Set Pilot — $299 one-time

A paid, manually supported inspection-readiness setup for one facility:

- Facility readiness binder created and configured
- Assisted-living starter checklist seeded automatically
- Document/evidence organization
- Open-item and corrective-action tracking
- Digital inspection-readiness report
- Paid PDF export
- One implementation/review session
- Clear statement that Ready Set is an independent readiness service, not ADHS and not a legal/compliance guarantee

### Starter — $19/month

For facilities that want to maintain the binder themselves after setup.

### Pro — $49/month

For customers that want the full current software workflow, paid reporting, reminders, and ongoing use while the next-generation findings/evidence platform is built.

> **Launch strategy:** sell the $299 paid pilot first. Use the recurring plans as the conversion path after the customer receives the first useful readiness report.

## What the current product does

- Register and log in
- Create facility binders
- Auto-seed an Assisted Living readiness checklist
- Track inspection, renewal, maintenance, training, and documentation tasks
- Upload PDF/JPG/PNG evidence with size and type limits
- Generate a safe HTML inspection-readiness report
- Export a paid PDF report
- Start Stripe checkout for paid plans
- Receive Stripe webhook updates to activate billing status
- Send protected reminder emails for upcoming/overdue tasks
- Monitor app health with `/health`, `/metrics`, and `/status`

## Positioning

Do **not** sell this as generic compliance software and do not promise that a facility will "pass" an ADHS survey.

Use this positioning:

> **Ready Set Solutions helps Arizona assisted-living operators identify, organize, document, and correct inspection-readiness gaps before an official survey.**

Recommended customer-facing disclaimer:

> Ready Set Solutions is an independent compliance-readiness and documentation service. It is not the Arizona Department of Health Services, does not conduct official regulatory inspections, does not provide legal advice, and does not guarantee a deficiency-free survey or any particular regulatory outcome. Facility owners and licensees remain responsible for determining and maintaining compliance with applicable requirements.

## Fast launch sequence

1. Deploy the current app to staging/production.
2. Configure real Stripe prices and the webhook.
3. Verify one complete checkout → webhook → paid PDF flow.
4. Configure real email delivery and verify reminder delivery.
5. Use durable storage and a tested backup/restore process before storing meaningful customer volume.
6. Sell three paid Ready Set Pilots before funding LiDAR or a larger sales team.
7. Have a trained Ready Set Readiness Specialist perform or support the walkthrough using the field SOP in `docs/READY_SET_FIELD_SOP.md`.
8. Deliver the report within 24 hours and convert useful pilots to recurring plans.

## Local quick start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
make install-dev
cp .env.example .env
make migrate
make run
```

Open: http://localhost:8000

Useful commands:

```bash
make install-dev
make validate-launch
make migrate
make test
make ci
```

First use:

1. Register.
2. Log in.
3. Create a binder using the facility name.
4. Choose `Assisted Living` to seed the starter readiness checklist.
5. Upload supporting documents/evidence that are authorized for this system.
6. Complete or update readiness tasks.
7. Open the readiness report.
8. Configure Stripe to enable checkout and paid PDF export.

## Billing setup

The current code uses three Stripe price keys:

- `Starter` — `$19/month`
- `Pro` — `$49/month`
- `Ready Set Pilot / Done-With-You Setup` — `$299 one-time`

Set:

```env
STRIPE_SECRET_KEY=sk_live_or_test_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_SETUP=price_...
PUBLIC_APP_URL=https://your-domain.com
```

Webhook endpoint:

```text
POST /billing/webhook
```

Recommended Stripe events:

- `checkout.session.completed`
- `customer.subscription.updated`
- `customer.subscription.deleted`

## Reminder setup

Protected reminder endpoint:

```text
POST /reminders/run
```

Required header:

```text
X-Cron-Secret: <REMINDER_CRON_SECRET>
```

Optional scheduled workflow:

```text
.github/workflows/reminders.yml
```

## Production environment

Set at minimum:

```env
ENV=production
SECRET_KEY=<strong-random-secret>
DATABASE_URL=<managed-postgres-url>
UPLOAD_DIR=/var/lib/compliancebinder/uploads
ALLOWED_ORIGINS=https://your-domain.com
PUBLIC_APP_URL=https://your-domain.com
```

Production rules:

- Never use `SECRET_KEY=CHANGE_ME_DEV_ONLY` in production.
- Never use wildcard `ALLOWED_ORIGINS` in staging/production.
- Require HTTPS.
- Use managed Postgres for customer data.
- Move uploads to S3-compatible/object storage before material customer scale.
- Back up database and uploads daily and test restore procedures.
- Do not intentionally store resident clinical records/PHI during the initial pilot phase.
- Avoid photographing residents or resident-identifying information during field walkthroughs.
- Review the privacy policy, terms, insurance, worker classification, and Arizona regulatory-content licensing questions before broad public rollout.

## Regulatory-content policy

The software should maintain **citations, independently written plain-language checklist questions, evidence requirements, source/version metadata, and verification dates** rather than blindly copying large blocks of regulatory text.

Every customer report should distinguish:

- observed condition,
- supporting evidence,
- applicable reference,
- recommended corrective action,
- responsible person,
- due date,
- verification status.

LiDAR and computer vision are future evidence tools, not launch requirements and not substitutes for verified measurements when a regulatory threshold is close.

## Security notes

- Passwords are hashed with bcrypt.
- Auth uses JWT bearer tokens.
- Uploads are limited by size and MIME type.
- Report HTML escapes user-provided values.
- PDF export is gated behind active/trialing billing status.
- Staging/production fail fast on unsafe origin/app URL settings.
- The product organizes readiness information; it does not provide legal or regulatory advice.

## Repo layout

```text
ComplianceBinder/
  backend/
    app/
      main.py
      models.py
      db.py
      security.py
      schemas.py
      templates.py
      static/
    alembic/
    scripts/
    tests/
    Makefile
    requirements.txt
    requirements-dev.txt
    .env.example
  docs/
  render.yaml
```

## Launch operating documents

- `docs/COMMERCIAL_LAUNCH.md` — 30-day launch and remote operating plan
- `docs/READY_SET_FIELD_SOP.md` — walkthrough and report-delivery procedure
- `docs/PILOT_SALES_PLAYBOOK.md` — target customer, pitch, qualification, objections, commission guardrails
- `docs/REGULATORY_CONTENT_POLICY.md` — rule-reference/versioning and liability guardrails

## Primary launch KPI

**Three paid Arizona assisted-living pilots, delivered without the founder needing to be onsite.**
