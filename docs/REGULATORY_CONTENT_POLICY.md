# Ready Set Solutions — Regulatory Content Policy

## Purpose

Ready Set reports must be useful without pretending that software-generated text is law. This policy controls how regulatory references enter the product, how they are reviewed, and what must happen before a customer-facing report is released.

## Source hierarchy

Use authoritative sources in this order:

1. **Arizona Secretary of State** — current Arizona Administrative Code and Administrative Register
2. **Arizona Legislature** — current Arizona Revised Statutes
3. **Arizona Department of Health Services** — official licensing guidance, provider information, survey/deficiency information and formal agency materials
4. Other government sources where directly applicable

Competitor websites, blogs, consultant pages, AI output and general web articles may be used to identify a research question, but **not as the final authority for a customer-facing rule citation**.

## Core rule

Every material regulatory reference in a final report must be checked against the current official source before release.

If verification is incomplete, mark the item:

> **Regulatory reference: Needs Review**

Do not guess.

## Regulatory record format

The future structured `RuleReference` model should contain at minimum:

- `citation`
- `short_title`
- `plain_language_summary`
- `applicability`
- `evidence_expected`
- `official_source`
- `source_url_or_identifier`
- `source_version`
- `effective_date`
- `last_verified_at`
- `verified_by`
- `status`
- `superseded_by`

Allowed status values should include:

- `verified`
- `needs_review`
- `superseded`
- `not_applicable`

## Plain-language summaries

Ready Set should write its own concise operational summary of a requirement rather than relying on long copied blocks of regulatory text.

A useful summary should answer:

- Who/what does this apply to?
- What must the facility be able to demonstrate?
- What evidence is relevant?
- What physical or documentation condition should the walkthrough check?
- What should be escalated for professional/legal interpretation?

The official authority controls if a Ready Set summary differs from the actual statute, rule, agency order or official interpretation.

## Commercial-use caution

Do not bulk-copy or commercially redistribute large portions of the Arizona Administrative Code inside the product until the commercial-use/licensing question has been reviewed and resolved.

Launch architecture should prefer:

> citation + independently written plain-language checklist + evidence requirement + source/version metadata + official source reference

rather than embedding full regulatory chapters.

## Report language

### Preferred

- "Observed condition"
- "Readiness finding"
- "Potential discrepancy"
- "Management review recommended"
- "Regulatory reference verified on [date]"
- "Verification required"
- "Corrective action recommended"

### Avoid unless qualified and specifically reviewed

- "Certified compliant"
- "Guaranteed compliant"
- "Violation confirmed"
- "ADHS approved"
- "This guarantees you will pass"
- "This prevents a fine"

## Required report disclaimer

> Regulatory citations and plain-language explanations are provided to assist the customer in organizing compliance-readiness activities. Ready Set Solutions is not ADHS and does not provide legal advice or guarantee regulatory outcomes. In the event of any difference between a Ready Set explanation and an official statute, rule, agency interpretation or order, the official authority controls. Regulatory requirements may change after the report date.

## Verification workflow

Before a final report:

1. Identify each material finding requiring a regulatory reference.
2. Open the current official source.
3. Confirm the citation is current and applies to the facility/situation.
4. Confirm Ready Set's plain-language summary does not overstate the requirement.
5. Record the verification date and reviewer.
6. Mark obsolete material `superseded`.
7. Stop report delivery if a critical reference remains uncertain.

## Update cadence

### Before every customer-facing final report

Verify the material citations actually used in that report.

### Weekly during active pilots

Review official Arizona rulemaking/licensing update channels for changes relevant to assisted living.

### Monthly

Review the checklist library for stale verification dates, duplicated items and rules that have changed applicability.

### Immediately

Review affected content after any known major statute/rule/licensing update or an ADHS communication that changes the operating assumptions.

## Current launch implementation

The current MVP stores readiness prompts in task titles/descriptions. That is acceptable for the first manually supported pilots because a human QA step verifies customer-facing references before final delivery.

It is **not** the final compliance-intelligence architecture.

## Phase 2 domain model

The next product iteration should separate:

- `Facility`
- `Inspection`
- `Finding`
- `Evidence`
- `RuleReference`
- `RuleVersion`
- `Measurement`
- `CorrectiveAction`
- `Verification`

This allows a finding to point to a versioned regulatory reference instead of burying rule text inside a task description.

## Evidence-to-rule integrity

A rule citation alone does not prove a finding.

A defensible finding requires:

> observed condition → evidence → applicable verified reference → plain-language explanation → corrective action → owner → due date → verification

If any link is missing, the report should clearly show the uncertainty instead of manufacturing certainty.

## Measurement policy

LiDAR, AR or computer vision may assist with screening and documentation later, but these technologies do not replace verified measurement for threshold-dependent conclusions.

When measurement error could change a regulatory conclusion:

- mark the finding `Verification Required`
- use the approved measurement procedure/instrument
- record the verified value and evidence
- confirm the current applicable threshold from the official source

## AI policy

AI may help:

- summarize already verified material
- suggest checklist wording
- categorize findings
- draft corrective-action language
- identify potential source updates for human review

AI may not autonomously:

- declare a facility legally compliant
- create an unsupported citation
- silently replace an official source
- issue a final measurement-based pass/fail conclusion without the required verification

## QA metrics

Target:

- **0 critical citation errors**
- **0 reports released with unresolved critical references**
- **100% of material final-report references with a verification date**
- **100% of superseded references removed from active use once identified**

A critical regulatory-reference error is a stop-ship and incident-review event.