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
- Monitor app health with `/health`, `/metrics`, and `/status`

## Local quick start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open: http://localhost:8000

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
- Put the app behind HTTPS.
- Use managed Postgres for serious customer volume.
- Move uploads to S3-compatible storage before scaling beyond the first few customers.
- Back up database and uploads daily.
- Add a privacy policy and terms page before broad launch.

## Existing database caveat

Fresh deployments create the billing columns automatically through SQLModel metadata. Existing MVP databases created before this launch branch may need additive billing columns added manually before using billing endpoints.

Required `user` table columns:

- `billing_plan`
- `billing_status`
- `stripe_customer_id`
- `stripe_subscription_id`
- `billing_updated_at`

For a clean first launch, use a fresh database unless you intentionally migrate old local data.

## Security notes

- Passwords are hashed with bcrypt.
- Auth uses JWT bearer tokens.
- Uploads are limited by size and MIME type.
- Report HTML escapes user-provided values.
- PDF export is gated behind active/trialing billing status.
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
    requirements.txt
    .env.example
  docs/
  scripts/
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
