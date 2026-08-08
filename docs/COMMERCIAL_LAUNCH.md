# Ready Set Solutions — 30-Day Commercial Launch

## Objective

Launch the existing ComplianceBinder product as a paid Arizona assisted-living inspection-readiness service and obtain **3 paid pilot facilities in 30 days** without requiring the founder to be onsite.

The launch is intentionally service-led. The software is the operating system; the paid readiness outcome is what is sold first.

## Launch offer

### Ready Set Pilot — $299 one-time

One facility receives:

- Ready Set facility account and readiness binder
- Arizona assisted-living starter readiness workflow
- Evidence/document organization
- Open-item and corrective-action tracking
- Readiness report in digital form
- Paid PDF report access
- One implementation/review session
- Optional field walkthrough support by a trained Ready Set Readiness Specialist

The $299 pilot uses the existing Stripe `setup` price key so it can launch without redesigning billing.

### Recurring conversion

After the pilot:

- **Starter — $19/month:** maintain the binder and workflow
- **Pro — $49/month:** current full software workflow, reminders and paid reporting

These prices are launch-compatible prices, not permanent market positioning. Re-price after the first 10 paying facilities using actual conversion, support-time, retention and willingness-to-pay data.

## Ideal first customers

Prioritize in this order:

1. Arizona assisted-living operators with 2–10 homes
2. Independent assisted-living homes with an owner/operator decision maker
3. Recently licensed or operationally changing facilities
4. Facilities with a near-term survey-readiness concern
5. Single-home operators who lack a formal compliance/readiness system

Start in one field-service territory, preferably Phoenix metro, so travel and dispatch remain controllable.

## 30-day execution

### Week 1 — Make the offer deliverable

- Deploy a production-like environment
- Configure Stripe test/live products and webhook
- Complete checkout → webhook → paid-access → PDF test
- Configure real outbound email and verify delivery
- Confirm customer-upload storage and backup process
- Create one demonstration facility
- Generate one excellent sample report
- Prepare an initial list of 80 target facilities
- Identify one field Readiness Specialist who can complete pilot walkthroughs without the founder

**Exit condition:** a customer can pay, receive access, complete the workflow, and receive a report.

### Week 2 — Prove the pitch

- Work the first 40 targeted facilities
- Reach at least 8 owner/manager conversations
- Conduct at least 3 fit calls/demos
- Close the first paid pilot
- Founder participates in early calls to learn objections and buying language
- Do not hire a salaried sales team

### Week 3 — Prove fulfillment

- Work the remaining 40 targets
- Complete 2–3 paid pilot engagements
- Have the Readiness Specialist follow the field SOP
- Deliver each final report within 24 hours after evidence is complete
- Record every customer question and every manual workaround
- Ask each satisfied pilot whether ongoing software would be useful

### Week 4 — Prove recurring value

- Convert at least 2 pilot customers to a recurring plan or obtain a specific reason they will not convert
- Standardize the report QA checklist
- Standardize scheduling and customer onboarding
- Document support requests and founder time
- Decide whether the next hire should be sales, operations or a second field specialist based on the actual bottleneck

## Remote operating model

### Founder

Own only:

- product priorities
- capital decisions
- weekly sales review
- high-risk regulatory/content QA
- major customer relationships

The founder should not become the scheduler, routine support desk, report formatter or default field worker.

### Technical contractor

Own:

- deployment
- uptime and application errors
- Stripe/webhook issues
- email/configuration issues
- backups/storage
- prioritized product changes

### Business-development partner

Own:

- target-account outreach
- appointment setting
- qualification
- follow-up

Compensation should be based on **collected revenue**, not signed promises. Never allow guarantees about passing an inspection or avoiding enforcement.

### Readiness Specialist

Own:

- onsite walkthrough
- evidence capture within approved scope
- measurement verification workflow
- finding notes
- submission of the completed field package

Pay for a completed, quality-reviewed engagement—not for the number or severity of findings.

### Virtual operations coordinator

Add after the first pilots if scheduling/admin becomes the constraint. Own:

- scheduling
- account setup
- customer reminders
- report assembly checklist
- billing follow-up
- routine customer-status communication

## Founder weekly cadence

A founder with a full-time day job should be able to operate the launch with three short control blocks:

1. **Pipeline review — 30 minutes:** prospects, conversations, demos, payments, next actions
2. **Delivery QA — 30 minutes:** reports due, high-priority findings, customer issues, field quality
3. **Product/regulatory review — 30 minutes:** bugs, content updates, repeated customer requests, stop-ship risks

Escalations can be handled separately, but ordinary fulfillment should not depend on the founder being available during business hours.

## Pilot KPIs

| KPI | 30-day target |
|---|---:|
| Targeted facilities worked | 80+ |
| Meaningful owner/manager conversations | 15+ |
| Fit calls/demos | 6+ |
| Paid pilots | **3+** |
| Pilot → recurring conversion | ≥50% |
| Report delivery after field package complete | ≤24 hr |
| Field-service contribution margin target | ≥40% |
| Critical regulatory-reference errors | **0** |
| Critical privacy/security incidents | **0** |
| Founder onsite visits required | **0** |

## Stop-ship conditions

Do not deliver a final customer report until resolved if any of these occur:

- a material regulatory citation has not been verified against the current official source
- evidence does not support the finding
- unnecessary resident-identifying or clinical information is included
- a measurement near a legal threshold has not been verified using the approved measurement procedure
- the report implies Ready Set is ADHS, an official inspector, a certifier or legal counsel
- payment/report-access behavior is broken
- customer data cannot be stored or recovered safely enough for the agreed pilot scope

## What not to build before 3 paid pilots

- custom tablet inventory program
- native LiDAR application
- autonomous AI compliance determinations
- resident EHR/eMAR functionality
- large sales team
- multi-state regulation engine
- complex enterprise integrations

## Day-30 decision

Continue and invest if the business demonstrates:

- 3+ paid pilots from a genuinely targeted first cohort
- customers value the final report
- at least 2 pilots show recurring interest
- field work can be completed without the founder
- delivery economics can plausibly maintain ≥40% contribution margin

If those conditions are not met, change the offer or customer segment before adding major engineering cost.