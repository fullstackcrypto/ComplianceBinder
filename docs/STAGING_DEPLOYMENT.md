# Staging Deployment Runbook

This runbook deploys InspectionBinder / ComplianceBinder to a staging environment before production launch.

## Recommended staging stack

Use the included Render blueprint unless you have a better reason not to.

- Web service: Render web service from `render.yaml`
- Database: Render managed Postgres
- File storage: Render persistent disk mounted at `/var/data`
- Payments: Stripe test mode
- Mail: SMTP-compatible provider in sandbox/test mode
- Monitoring: uptime check against `/health`

## Render blueprint

The repo includes:

```text
render.yaml
```

It defines:

- staging web service
- managed Postgres database
- persistent upload disk
- build command: `pip install -r requirements-dev.txt`
- pre-deploy migration command: `alembic upgrade head`
- start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Required staging environment

Set these variables in Render after creating the blueprint service:

```env
ENV=staging
SECRET_KEY=<strong random staging signing key>
DATABASE_URL=<provided by Render Postgres>
UPLOAD_DIR=/var/data/uploads
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

Generate secrets locally with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Manual build/start commands

If not using Render blueprint:

Build:

```bash
cd backend && pip install -r requirements-dev.txt
```

Pre-deploy migration:

```bash
cd backend && alembic upgrade head
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
8. Try PDF export before payment; it should be blocked.
9. Start Stripe test checkout.
10. Complete payment with Stripe test card.
11. Confirm `/billing/status` shows active or trialing.
12. Download PDF report.
13. Call `/reminders/run` with the configured `X-Cron-Secret` header.
14. Confirm reminder response returns `ok: true` or dry-run output in staging.

## Scheduled reminders from GitHub Actions

The repo includes:

```text
.github/workflows/reminders.yml
```

Set these repository secrets only after staging exists:

```text
STAGING_APP_URL=https://<staging-domain>
REMINDER_CRON_SECRET=<same value used by Render>
```

The workflow runs daily and can also be triggered manually.

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
- Cancellation removes PDF access.
- Reminder job runs without authentication failure.
- Privacy and terms pages are reachable.
- Uploaded files persist after redeploy.
