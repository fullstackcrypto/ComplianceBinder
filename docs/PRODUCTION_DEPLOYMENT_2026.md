# Ready Set Solutions — Production Deployment 2026

This runbook is the production source of truth for deploying ComplianceBinder for the Arizona assisted-living paid pilot.

## Architecture

- App: Render web service `ready-set-compliancebinder`
- Customer URL: `https://app.charleysllc.com`
- Database: paid Render Postgres `ready-set-compliancebinder-db`
- Evidence storage: encrypted Render persistent disk mounted at `/var/data`
- Reminder scheduler: Render Cron Job `ready-set-reminders`
- Billing: Stripe Checkout + verified webhooks
- Transactional reminders: Namecheap Private Email over authenticated encrypted SMTP
- CI/security: GitHub Actions, Bandit, pip-audit, CodeQL, Gitleaks, Render Blueprint validation, production DAST after launch

## 1. Create the Render Blueprint

Use Render's Blueprint flow and connect this repository:

`https://github.com/fullstackcrypto/ComplianceBinder`

The repository root contains `render.yaml`. Review the plan before approving creation.

The Blueprint intentionally:

- deploys `main` only after GitHub checks pass,
- uses the production dependency set,
- runs configuration validation and Alembic migrations before deployment,
- generates internal application/monitoring/cron secrets,
- keeps third-party Stripe and mail credentials out of Git,
- gives Postgres no public IP allow-list entries,
- mounts customer evidence under `/var/data`,
- creates a daily reminder Cron Job,
- declares `app.charleysllc.com` as the app domain.

## 2. Supply third-party secrets during first Blueprint sync

Render will prompt for every variable declared with `sync: false`.

### Stripe

Enter values directly from the Stripe Dashboard; never copy them into GitHub:

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET` — create this after the production endpoint exists, then update the service
- `STRIPE_PRICE_STARTER`
- `STRIPE_PRICE_PRO`
- `STRIPE_PRICE_SETUP`

Use Stripe test mode for acceptance first. Move to live-mode credentials only after the complete test transaction and cancellation paths pass.

### Email

- `REMINDER_FROM_EMAIL` — recommended: `Ready Set Solutions <support@charleysllc.com>`
- `MAIL_USER` — full Private Email mailbox address
- `MAIL_KEY` — application password when supported by the mailbox plan; otherwise the credential required by the current Private Email account

The Blueprint uses:

- host `mail.privateemail.com`
- port `587`
- STARTTLS enabled
- SMTP authentication required

The code also supports implicit TLS on port 465 by switching `MAIL_PORT=465`, `MAIL_USE_TLS=false`, `MAIL_USE_SSL=true` if required.

## 3. Authenticate the sending domain

Before relying on customer reminders, verify the exact current records shown in the Namecheap Private Email dashboard.

For Namecheap Private Email, the normal SPF record is:

`v=spf1 include:spf.privateemail.com ~all`

DKIM hostname depends on the Private Email subscription generation:

- plans purchased on/after June 2, 2026: `privateemail._domainkey`
- legacy plans purchased before June 2, 2026: `default._domainkey`

Copy the unique DKIM value from the Namecheap account; do not invent it.

Start DMARC in monitoring mode unless the complete set of legitimate senders for `charleysllc.com` has already been verified. A typical initial record is:

`v=DMARC1; p=none; rua=mailto:postmaster@charleysllc.com`

Tighten DMARC only after confirming all authorized senders align with SPF/DKIM.

## 4. Point the app domain to Render

After the web service is created, use the exact DNS target Render displays for the custom domain `app.charleysllc.com`.

Do not guess the target. Wait until Render reports the custom domain verified and HTTPS is active.

## 5. Create the Stripe webhook

Create a Stripe webhook endpoint at:

`https://app.charleysllc.com/billing/webhook`

Subscribe to the events the application handles:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `checkout.session.async_payment_failed`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_failed`

Copy the resulting `whsec_...` signing secret into `STRIPE_WEBHOOK_SECRET` in Render and redeploy.

## 6. Production acceptance — do not skip

Use a new external test customer and perform the full flow.

### Account and data isolation

1. Register and log in.
2. Create an Assisted Living binder.
3. Confirm the starter tasks are present.
4. Upload a small authorized PDF/JPG/PNG.
5. Confirm the document can be downloaded by its owner.
6. Confirm a second user cannot access the first user's binder or file.

### Billing

1. Start the $299 Ready Set Pilot Checkout.
2. Complete payment in Stripe test mode.
3. Confirm the webhook changes billing status without any manual database edit.
4. Confirm paid PDF export succeeds.
5. Confirm an unpaid/failed Checkout does not grant access.
6. Test Starter and Pro subscription activation.
7. Test failed-payment and cancellation state changes.
8. Repeat the critical path once with live Stripe mode before accepting a real customer.

### Email

1. Create a due task within the reminder window.
2. Run the reminder job.
3. Confirm delivery to at least two external mailbox providers.
4. Inspect message headers for SPF, DKIM and DMARC results.
5. Confirm a failed SMTP login produces a failed job instead of pretending delivery succeeded.

### Storage and recovery

1. Upload a test evidence file and record its document ID.
2. Restart/redeploy the web service and confirm the file remains available.
3. Create/identify a persistent-disk snapshot.
4. Deliberately alter or remove test-only evidence and restore the disk snapshot.
5. Confirm the recovered file hash/content matches the original.
6. Create test-only database records.
7. Perform a Render Postgres point-in-time recovery into a new database.
8. Verify the restored records before changing any production connection string.
9. Create and download a logical Postgres export for an additional portable recovery artifact.

Issue #12 is not complete until an actual restore has been performed successfully.

## 7. Activate external production security scanning

After the production URL is live, set the GitHub Actions secret:

`PRODUCTION_APP_URL=https://app.charleysllc.com`

The scheduled DAST workflow then checks production security headers/exposure and runs the OWASP ZAP baseline scan.

## 8. Launch gate

Do not onboard a paid facility until all of these are true:

- `main` CI is green
- CodeQL is green
- Gitleaks is green
- Render Blueprint validation is green
- HTTPS custom domain works
- `/health` is healthy
- production API docs are not publicly exposed
- `/metrics` and `/status` reject unauthenticated requests
- $299 test Checkout completes end to end
- failed/unpaid Checkout cannot grant access
- subscription cancellation removes paid state as expected
- external reminder email is received and authenticated
- customer evidence survives a deployment/restart
- evidence snapshot restore has been tested
- Postgres PITR or backup restoration has been tested
- no unnecessary resident clinical information/PHI is used in the pilot test

## Scaling note

The persistent disk is appropriate for the initial controlled pilot, but it keeps the web service stateful. Before material multi-instance scale, migrate customer evidence to managed object storage with versioning and independent backup controls. Keep the database on managed Postgres.
