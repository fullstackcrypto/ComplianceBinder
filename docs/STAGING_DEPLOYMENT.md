# Staging Deployment Runbook

This runbook deploys InspectionBinder / ComplianceBinder to a staging environment before production launch.

## Recommended staging stack

Use a boring managed stack:

- Web service: Render, Railway, Fly.io, or a small VPS
- Database: managed Postgres
- File storage: local disk for staging only; S3-compatible storage before broader production use
- Payments: Stripe test mode
- Mail: SMTP-compatible provider in sandbox/test mode
- Monitoring: uptime check against `/health`

## Required staging environment

Set these variables in the staging host:

```env
ENV=staging
SECRET_KEY=<strong random staging signing key>
DATABASE_URL=<staging postgres connection string>
UPLOAD_DIR=/var/lib/inspectionbinder/uploads
ALLOWED_ORIGINS=https://<staging-domain>
PUBLIC_APP_URL=https://<staging-domain>

STRIPE_SECRET_KEY=<Stripe test-mode secret key>
STRIPE_WEBHOOK_SECRET=<Stripe webhook signing secret>
STRIPE_PRICE_STARTER=<Stripe test price for $19/mo Starter>
STRIPE_PRICE_PRO=<Stripe test price for $49/mo Pro>
STRIPE_PRICE_SETUP=<Stripe test price for $299 one-time setup>

REMINDER_CRON_SECRET=<strong random reminder job token>
REMINDER_WINDOW_DAYS=7
REMINDER_FROM_EMAIL=InspectionBinder <no-reply@your-domain>
MAIL_HOST=<smtp host>
MAIL_PORT=587
MAIL_USER=<smtp user>
MAIL_KEY=<smtp api key or password>
MAIL_USE_TLS=true
```

## Build/start commands

From the `backend` directory:

```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

For a deployment platform with separate build/start commands:

Build:

```bash
cd backend && pip install -r requirements-dev.txt && alembic upgrade head
```

Start:

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Staging smoke test

1. Open the staging URL.
2. Confirm `/health` returns `healthy` or `degraded` with database reachable.
3. Register a test user.
4. Create an Assisted Living binder.
5. Confirm starter tasks are created.
6. Upload a small PDF.
7. Confirm HTML report opens.
8. Start Stripe test checkout.
9. Complete payment with Stripe test card.
10. Confirm `/billing/status` shows active or trialing.
11. Download PDF report.
12. Call `/reminders/run` with the configured `X-Cron-Secret` header.
13. Confirm reminder response returns `ok: true` or dry-run output in staging.

## Monitoring

Configure uptime checks for:

```text
GET /health
```

Optional internal checks:

```text
GET /metrics
GET /status
```

## Launch gate

Do not promote staging to production until:

- CI passes.
- Alembic migration runs cleanly.
- Stripe test checkout activates billing.
- Paid PDF export works.
- Reminder job runs without authentication failure.
- Privacy and terms pages are reachable.
