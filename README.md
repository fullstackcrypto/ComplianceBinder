[![CI](https://github.com/fullstackcrypto/ComplianceBinder/actions/workflows/ci.yml/badge.svg)](https://github.com/fullstackcrypto/ComplianceBinder/actions/workflows/ci.yml)

# InspectionBinder / ComplianceBinder

A focused digital inspection binder SaaS for small operators who need documents, tasks, and reports ready before an inspection.

Current first wedge: **assisted living / small care homes**.

## What it does

- Register and log in
- Create binders
- Auto-seed an Assisted Living starter checklist
- Track inspection and renewal tasks
- Upload PDF/JPG/PNG documents with size and type limits
- Generate a safe HTML inspection report
- Export a paid PDF inspection report
- Start Stripe checkout for paid plans
- Receive Stripe webhook updates to activate billing status
- Send protected reminder emails for upcoming/overdue tasks
- Monitor app health with `/health`, `/metrics`, and `/status`

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

Useful backend commands:

```bash
make install-dev      # install app, test, and migration dependencies
make validate-launch # validate deployed environment variables
make migrate         # run Alembic migrations
make test            # run launch test suite
make ci              # run install, config validation, migrations, and tests
```

First use:

1. Register.
2. Log in.
3. Create a binder.
4. Choose `Assisted Living` to seed the starter checklist.
5. Upload documents.
6. Open the inspection report.
7. Configure Stripe to enable checkout and paid PDF export.

## Billing setup

Create three Stripe prices:

- `Starter` — `$19/month`
- `Pro` — `$49/month`
- `Done-With-You Setup` — `$299 one-time`

Then set these environment variables:

```env
STRIPE_SECRET_KEY=sk_live_or_test_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_SETUP=price_...
PUBLIC_APP_URL=https://your-domain.com
```

Stripe webhook endpoint:

```text
POST /billing/webhook
```

Recommended Stripe events:

- `checkout.session.completed`
- `customer.subscription.updated`
- `customer.subscription.deleted`

## Reminder setup

The protected reminder endpoint is:

```text
POST /reminders/run
```

Required header:

```text
X-Cron-Secret: <REMINDER_CRON_SECRET>
```

The repo includes an optional scheduled GitHub Actions workflow:

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

Production notes:

- Do not run production with `SECRET_KEY=CHANGE_ME_DEV_ONLY`.
- Do not run staging/production with wildcard `ALLOWED_ORIGINS`.
- Put the app behind HTTPS.
- Use managed Postgres for serious customer volume.
- Move uploads to S3-compatible storage before scaling beyond the first few customers.
- Back up database and uploads daily.
- Review privacy and terms pages before broad launch.

## Database and migrations

Local/dev/test environments can create tables automatically for convenience.

Staging and production must use Alembic:

```bash
cd backend
make migrate
```

Render staging runs migration as a pre-deploy command through `render.yaml`.

## Security notes

- Passwords are hashed with bcrypt.
- Auth uses JWT bearer tokens.
- Uploads are limited by size and MIME type.
- Report HTML escapes user-provided values.
- PDF export is gated behind active/trialing billing status.
- Staging/production fail fast on unsafe origin/app URL settings.
- This product organizes inspection documents; it does not provide legal or regulatory advice.

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

## Monitoring

```text
GET /health
GET /metrics
GET /status
```

These endpoints support uptime checks and basic system visibility.

## Launch offer

Recommended first sales offer:

> I set up your inspection-ready digital binder for $299. After that, it is $49/month for hosting, reminders, reports, and updates.

Do not position this as generic compliance software. Sell the outcome: **inspection-ready binders for small operators.**
