# Ready Set Solutions Security Operations

## Launch security objective

Protect customer accounts, facility documents, uploaded evidence, billing state, and operational data while keeping the public attack surface as small as practical.

## Automated assurance

- Every merge to `main`: tests, migrations, Bandit static analysis, and `pip-audit` dependency auditing.
- Weekly: the full CI suite reruns even without code changes so newly disclosed dependency issues can fail the build.
- Weekly: Gitleaks scans the complete Git history for secret patterns.
- Weekly: CodeQL performs semantic Python security analysis.
- Weekly after `PRODUCTION_APP_URL` is configured: HTTPS/header checks and an OWASP ZAP passive baseline scan.
- Dependabot checks Python and GitHub Actions dependencies weekly.

## Secrets

Production secrets belong only in the hosting/GitHub encrypted secret stores. Never commit or paste into source control:

- `SECRET_KEY`
- Stripe secret key or webhook signing secret
- SMTP/mailbox password
- database credentials
- monitoring/reminder secrets
- Namecheap credentials or recovery codes
- private keys or access tokens

If a real secret is ever committed, assume it is compromised and rotate it. Removing a later commit is not sufficient because Git history may retain it.

## Customer-data handling

- Collect the minimum necessary data.
- Do not request resident clinical records or PHI by default.
- Customer binder/document access must remain owner-scoped.
- Uploaded files remain private and are served only after authorization.
- Sensitive application responses use `Cache-Control: no-store`.
- Do not log raw customer email addresses, facility names, filenames, passwords, tokens, or document contents.

## Uploads

Current defenses include file-size limits, allowed extensions/MIME types, magic-byte verification, random internal filenames, restrictive filesystem permissions, and owner-only download authorization.

Future production defense-in-depth should add malware scanning before files are made available and object-storage encryption/versioning when scale justifies migration from a persistent disk.

## Incident response

1. Stop the affected feature or deployment if active exposure is plausible.
2. Preserve logs without copying customer document contents into tickets or chat.
3. Rotate any potentially exposed credential immediately.
4. Identify affected accounts/data and the exposure window.
5. Patch in an isolated branch and run the full security suite.
6. Restore from a known-good backup when integrity is uncertain.
7. Document root cause, customer impact, and a prevention control.
8. Notify affected parties when legally or contractually required.

## Production gates

Do not call the service production-ready until all are verified against the real environment:

- HTTPS custom domain
- strong production-only secrets
- managed database
- durable private upload storage
- Stripe live webhook and end-to-end checkout
- SMTP delivery with SPF, DKIM, and DMARC verified
- database and upload backups
- actual restore drill
- external account-isolation tests
- security headers and disabled production API docs
- scheduled production security scan

## Review cadence

Review security findings and failed automated checks before feature work. High-severity findings, data-isolation failures, leaked credentials, payment-access bypasses, and backup/restore failures are stop-ship conditions.
