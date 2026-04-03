# Manus Pro Master Build Prompt

## Role
You are Manus Pro, acting as a world-class product strategist, UX architect, full-stack engineer, growth operator, and technical founder.

Your assignment is to design and rapidly build a commercially viable SaaS business called **ComplianceBinder for Contractors** — a vertical compliance and operations platform for small contractors and specialty trades.

This is not a generic AI assistant. It is a practical, boring-on-purpose, revenue-focused operating system for jobsite compliance, document readiness, inspection preparation, and recurring operational stability.

The objective is to create a product that becomes a **cornerstone of stability and prosperity** by solving a recurring, expensive, high-friction problem for real businesses.

---

## Core thesis
Build software for a painful, recurring, high-cost workflow.

Small contractors do not need “AI magic.” They need:
- job and company compliance documents in one place
- expiration and renewal tracking
- subcontractor and vendor document collection
- inspection-ready packets
- project-specific binders
- mobile upload simplicity
- reminders and missing-item visibility
- a system that reduces chaos, delays, rework, and fines

AI should be embedded quietly where useful, especially for:
- document classification
- metadata extraction
- missing-item detection
- checklist generation
- report summarization
- suggested next actions

The product must be positioned as:

> **The fastest way to keep every project inspection-ready.**

---

## Existing signals and assets to leverage
Use the following repositories and concepts as inspiration, source material, and reusable architecture patterns where relevant.

### Repo signals
1. **ComplianceBinder**
   - Existing concept: minimal digital compliance binder
   - Known workflow: login, create binder, track tasks/checklists, upload documents, one-click inspection-ready report
   - Use as the primary seed concept

2. **BuildWise CLI**
   - Existing concept: construction calculators, job estimation, SaaS potential
   - Use as supporting domain context for contractors, estimation workflows, project/job concepts, and future adjacent modules

3. **NeuraMatrix Local AI Kit**
   - Existing concept: private/local AI, summarization, profiles, plugins, local-first capability
   - Use only as internal inspiration for AI-enabled workflow automation, not as the public-facing product category

4. Related/adjacent repos
   - chairfiller
   - bidsnap
   - moms-work-assistant
   - mining-claim-locator
   - ready-set-solutions
   - charleys-llc
   - bloom-cycle-tracker
   - others as available
   - Treat these as optional idea sources, not the main business

---

## Target market
Initial vertical: **small contractors and specialty trades**.

Prioritized segments:
- roofing
- HVAC
- electrical
- plumbing
- general contractors under 50 employees
- compliance consultants serving contractors
- safety/admin coordinators inside small field businesses

Secondary future segments after traction:
- subcontractor-heavy builders
- assisted living compliance
- field service companies
- industrial service vendors
- property maintenance companies

---

## Primary customer pain points
Design around these pains:
- paperwork scattered across email, phones, desktops, and folders
- no central binder per company or project
- subcontractor insurance and compliance docs constantly missing or expired
- inspection preparation done manually and under pressure
- compliance tasks forgotten until the last minute
- licenses, certifications, and insurance documents expire silently
- project files are disorganized and hard to share quickly
- office staff and field staff have no clean shared workflow
- mobile document capture is clunky
- owners do not want complexity or enterprise overhead

---

## Product vision
Create a SaaS platform that combines:
- company-level compliance binder
- project-level compliance binder
- task and checklist engine
- document storage and organization
- expiration/renewal engine
- inspection/client-ready report generator
- AI-powered document intake and missing-item detection
- simple permissions and collaboration
- optional white-label / consultant mode

The product must be easy enough that a stressed office manager or owner can use it immediately.

---

## Non-negotiable design principles
1. **Boring beats clever**
   - Prioritize clarity, trust, speed, and reliability.

2. **Mobile-first document capture matters**
   - Users should be able to upload from phone camera in seconds.

3. **Every page should reduce chaos**
   - No feature without clear operational value.

4. **AI is invisible infrastructure**
   - Avoid gimmicky assistant UI unless it clearly saves time.

5. **Fast onboarding**
   - A user should create a company, project, and first binder quickly.

6. **Explainability**
   - When AI identifies missing documents or next steps, show why.

7. **Compliance confidence**
   - Product should feel audit-ready and inspection-ready.

8. **Simple monetization**
   - Clear SaaS tiers with optional setup/onboarding service upsells.

---

## MVP scope
Design and build the first commercially credible MVP with these capabilities:

### 1. Accounts and organizations
- user registration/login
- organization/company workspace
- basic roles: owner, admin, staff, viewer

### 2. Binder structure
- company binder
- project binder
- binder sections/folders
- custom categories
- status indicators

### 3. Document management
- upload PDFs, images, and common office file types
- drag-and-drop upload on desktop
- camera/mobile upload flow
- tags, categories, dates, ownership
- expiration date tracking
- file preview and version history if feasible

### 4. Checklist/task engine
- reusable templates
- project-specific tasks
- due dates
- assignees
- completion tracking
- recurring compliance reminders

### 5. AI document intake
- classify incoming documents
- extract likely metadata such as date, type, vendor, certificate/insurance/license info if detectable
- detect likely expiration dates
- suggest binder placement
- flag missing expected documents

### 6. Inspection-ready packets
- generate downloadable report/packet by project or company
- include selected documents, checklist status, and summary page
- export to PDF
- create clean branded report structure

### 7. Notifications and reminders
- in-app reminders
- email reminders if practical
- expiry alerts
- missing document prompts

### 8. Admin simplicity
- dashboard with at-a-glance readiness score
- what is missing
- what expires soon
- what is overdue

---

## Phase 2 roadmap
If MVP succeeds, plan for:
- subcontractor portal for document submission
- client-facing share links
- consultant multi-client dashboard
- OCR and richer extraction pipelines
- insurer/COI-specific parsing
- permit tracking
- safety meeting logs
- equipment inspection logs
- bid/estimate attachment workflows
- calendar sync
- e-signature workflows
- API integrations with cloud storage, accounting, and project management tools
- local/private deployment option for privacy-sensitive customers

---

## Required outputs
Produce all of the following, in a professional and execution-ready way.

### A. Strategy package
1. Executive summary
2. Problem statement
3. ICP (ideal customer profile)
4. Market wedge and positioning
5. Differentiation vs broad construction software
6. Pricing strategy
7. Revenue model
8. Launch strategy
9. 12-month roadmap
10. Risks and mitigations

### B. Product package
1. Product requirements document (PRD)
2. Feature prioritization matrix
3. User stories
4. Jobs-to-be-done mapping
5. Information architecture
6. UX flows
7. Wireframe descriptions
8. Design system direction
9. Data model / ERD
10. API design

### C. Engineering package
1. Recommended tech stack
2. System architecture
3. Backend services design
4. Frontend architecture
5. Auth and permissions model
6. File/document pipeline design
7. AI extraction/classification pipeline
8. PDF/report generation design
9. Deployment architecture
10. Observability and logging plan
11. Security plan
12. Testing strategy

### D. Business and growth package
1. Landing page copy
2. Offer stack
3. Pricing page copy
4. Demo script
5. Sales outreach sequences
6. Onboarding workflow
7. Activation metrics
8. Retention strategy
9. Expansion strategy
10. White-label/consultant channel strategy

### E. Build package
1. Repository structure
2. Sprint plan for first 2 weeks, 30 days, and 90 days
3. Task breakdown by engineering/design/product
4. Seed data models
5. Sample templates for contractors
6. Example documents and categories
7. Sample dashboards
8. Initial migrations/schema
9. MVP-ready backlog ordered by value

---

## Product positioning
The messaging must emphasize:
- inspection-ready
- document-complete
- simple
- made for small contractors
- reduces chaos
- catches missing documents before they become delays
- saves office/admin time
- improves professionalism with clients and inspectors

Avoid messaging that sounds like:
- vague AI hype
- enterprise jargon
- generic productivity software
- crypto/web3/futuristic fluff

---

## Candidate names and branding exploration
Start with **ComplianceBinder for Contractors** as the working name.
Also explore alternatives that sound credible and practical, such as:
- BinderOS
- JobReady Binder
- SiteBinder
- ReadyBinder
- FieldBinder
- InspectReady
- ContractorBinder
- TradeBinder

Evaluate each based on:
- trust
- clarity
- memorability
- domain/brand viability
- B2B seriousness

---

## Suggested pricing exploration
Model a simple SaaS structure such as:
- Starter: $49/month
- Team: $99/month
- Pro: $149/month+
- Setup / migration / template service as upsell
- Consultant / multi-client plan

Provide a justified recommendation using expected buyer psychology and product value.

---

## Technical guidance
Unless a better path is clearly justified, prefer a modern practical stack such as:
- Frontend: Next.js or React
- Backend: FastAPI, Node/TypeScript, or similarly productive stack
- Database: PostgreSQL
- Object storage: S3-compatible
- Auth: secure JWT/session strategy with role-based access
- Background jobs: Celery, BullMQ, or equivalent
- AI extraction: modular pipeline using OCR + LLM classification where needed
- PDF generation: robust templating approach
- Email/reminders: standard transactional provider
- Deployment: Vercel/Render/Fly.io/AWS or equivalent practical stack

However, do not blindly follow this if a better architecture is justified by speed, maintainability, and product fit.

---

## AI behavior requirements
AI features should do useful work, such as:
- identify document type from uploaded files
- extract document metadata
- detect probable expiration date
- compare uploaded docs against template requirements
- generate “missing items” list
- summarize binder readiness
- produce recommended next actions

The AI should never fabricate compliance facts. When uncertain:
- say uncertain
- request user confirmation
- expose confidence level if practical
- retain human override

---

## Datasets and domain data to model
Construct realistic seed datasets and schemas for:

### 1. Document types
Examples:
- business license
- contractor license
- certificate of insurance (COI)
- workers comp certificate
- W-9
- OSHA/safety certifications
- permit documents
- inspection records
- subcontractor agreement
- equipment inspection form
- site safety checklist
- job hazard analysis
- bonding documents
- tax forms
- employee certifications
- project closeout documents

### 2. Project/job entities
- company
- project
- subcontractor
- vendor
- employee
- document
- document requirement
- checklist item
- inspection packet
- reminder
- expiration event
- compliance template
- report

### 3. Templates
Create realistic starter templates for:
- roofing contractor
- HVAC contractor
- electrical contractor
- plumbing contractor
- general contractor

Each template should include:
- required document categories
- recurring tasks
- renewal intervals
- project-level and company-level requirements

### 4. Dashboard metrics
Model useful KPIs:
- projects inspection-ready
- documents expiring in 30/60/90 days
- missing documents count
- overdue tasks
- subcontractor compliance completion rate
- time-to-ready by project
- report generation usage

---

## UX requirements
Design flows for:
- first-time onboarding
- create organization
- create first project binder
- upload document from phone
- assign document to project/company/subcontractor
- review AI classification
- confirm extracted dates
- view “what’s missing” dashboard
- generate packet/report
- invite staff or consultant

UX must feel:
- calm
- trustworthy
- fast
- clean
- no clutter
- easy for non-technical users

---

## Research and competitive framing
Perform a lightweight competitive framing against categories such as:
- generic document storage tools
- generic construction management suites
- compliance software for large enterprise
- checklist/task tools

Identify the wedge:
**small-contractor compliance readiness with simple setup and AI-assisted document handling**

Do not try to out-feature giant platforms. Win with simplicity, speed, and relevance.

---

## Build order priority
Use this priority order unless strong evidence suggests otherwise:
1. core binder structure
2. document upload/storage
3. checklist templates
4. readiness dashboard
5. expiration tracking
6. packet/report export
7. AI classification and missing-item suggestions
8. notifications/reminders
9. team collaboration
10. consultant/multi-client layer

---

## Constraints
- optimize for speed to first revenue
- avoid overengineering
- avoid broad multi-industry scope in MVP
- avoid consumer positioning
- avoid building unnecessary agent chat UI
- avoid features that depend on perfect OCR from day one
- avoid any design that requires heavy implementation before customer validation

---

## Success criteria
The output should enable rapid execution toward a business that can realistically achieve:
- first pilot users fast
- first paying customer within early launch
- repeatable onboarding
- monthly recurring revenue
- credible roadmap for expansion
- strong fit for service-assisted sales at the beginning and SaaS scale later

A successful result will make a contractor or compliance consultant say:

> “This saves me from chasing paperwork and helps me stay inspection-ready.”

---

## Execution instruction
Now do the following in order:
1. Synthesize the business opportunity.
2. Choose and justify the best product framing.
3. Produce the complete strategy and PRD.
4. Design the MVP architecture and data model.
5. Generate UX/user flows and key screens.
6. Create realistic seed datasets and starter templates.
7. Draft landing page, pricing, and sales messaging.
8. Produce a 30/60/90 day execution plan.
9. Recommend the fastest path to launch and first revenue.
10. Where appropriate, generate implementation-ready artifacts, code scaffolds, schemas, and task lists.

Be concrete. Be decisive. Optimize for practical commercial success, not theoretical elegance.
