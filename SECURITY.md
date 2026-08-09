# Security Policy

Ready Set Solutions treats facility documents, customer contact information, uploaded evidence, authentication material, and billing identifiers as sensitive information.

## Report a security issue privately

Do **not** open a public GitHub issue containing a vulnerability, credential, customer record, facility document, resident information, exploit details, or screenshots of sensitive data.

Send a concise report to **support@charleysllc.com** with the subject `SECURITY: ComplianceBinder` and include only the minimum information needed to reproduce the issue. Never send production passwords, API keys, card data, or resident clinical information by email.

## Scope

Security reports may cover authentication, authorization, customer-data isolation, uploads/downloads, billing state, webhook handling, privacy exposure, dependency vulnerabilities, deployment configuration, or other behavior that could affect confidentiality, integrity, or availability.

## Data-minimization rule

ComplianceBinder is not intended to be a system of record for resident clinical data. Users should not upload unnecessary protected health information, government identifiers, payment-card data, passwords, access tokens, private keys, or other secrets.

## Automated security controls

The repository runs regression tests, static analysis, dependency auditing, full-history secret scanning, CodeQL analysis, and—once a production URL is configured—a scheduled OWASP ZAP passive baseline scan.

No automated control makes a service invulnerable. Production launch also requires secure hosting configuration, protected secrets, durable backups with a tested restore path, verified email/DNS authentication, and external end-to-end acceptance testing.
