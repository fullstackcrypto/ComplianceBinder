# Launch Status

This document tracks the launch-critical checklist requested for InspectionBinder / ComplianceBinder.

## 1. Tests

Status: **implemented, pending CI verification**

Implemented:

- `backend/tests/test_launch_flow.py`
- `.github/workflows/ci.yml`
- `backend/requirements-dev.txt`

Covered:

- health endpoint responds
- Assisted Living binder seeds template tasks
- report HTML escapes user content
- unpaid PDF export is blocked
- unsupported upload type is rejected
- reminder job requires authorization/config
- privacy and terms pages exist

Run locally:

```bash
cd backend
pip install -r requirements-dev.txt
alembic upgrade head
pytest -q
```

## 2. Alembic migrations

Status: **implemented**

Implemented:

- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/20260426_0001_initial_launch_schema.py`

Run:

```bash
cd backend
alembic upgrade head
```

## 3. Email reminders

Status: **implemented, requires mail provider configuration**

Implemented:

- `backend/app/mailer.py`
- `backend/app/reminders.py`
- reminder router mounted through monitoring router
- protected endpoint: `POST /reminders/run`

Required header:

```text
X-Cron-Secret: <REMINDER_CRON_SECRET>
```

Required environment:

```env
REMINDER_CRON_SECRET=<strong random token>
REMINDER_WINDOW_DAYS=7
REMINDER_FROM_EMAIL=InspectionBinder <no-reply@your-domain>
MAIL_HOST=<smtp host>
MAIL_PORT=587
MAIL_USER=<smtp user>
MAIL_KEY=<smtp key>
MAIL_USE_TLS=true
```

If mail is not configured, the reminder job returns dry-run output instead of sending.

## 4. Privacy/terms pages

Status: **implemented**

Implemented:

- `/privacy.html`
- `/terms.html`

Files:

- `backend/app/static/privacy.html`
- `backend/app/static/terms.html`

## 5. Stripe test mode

Status: **documented, requires Stripe account configuration**

Implemented:

- Stripe checkout endpoint
- Stripe webhook endpoint
- plan/status metadata
- paid PDF export gate
- runbook: `docs/STRIPE_TEST_MODE.md`

Manual required:

- create Stripe test products/prices
- configure environment variables
- configure webhook endpoint
- run payment-to-PDF acceptance test

## 6. Deploy staging

Status: **blueprint and runbook added, requires hosting account execution**

Implemented:

- `render.yaml`
- `docs/STAGING_DEPLOYMENT.md`

Manual required:

- connect repository to Render or equivalent host
- set secret environment variables
- deploy staging service
- confirm `/health`

## 7. Full payment-to-PDF test

Status: **documented, cannot execute without live staging + Stripe test credentials**

Implemented:

- `docs/PAYMENT_TO_PDF_TEST.md`

Pass criteria:

- unpaid PDF export is blocked
- Stripe test checkout succeeds
- webhook activates billing
- paid PDF export downloads
- canceled subscription removes access

## Remaining hard blockers before public launch

These are still real blockers:

1. CI must pass on GitHub Actions.
2. Staging environment must be deployed.
3. Stripe test prices and webhook secret must be configured.
4. Payment-to-PDF test must pass end-to-end.
5. Email provider must be configured and reminder job tested.
6. Production storage strategy must be chosen before uploading real customer documents at scale.

## Ruthless launch rule

Do not sell broad public access until the payment-to-PDF test passes. A done-with-you pilot can start earlier, but only with manual support and clear expectations.
