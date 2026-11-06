# 30-60-90 Day Implementation & Phased Rollout Roadmap

**Role:** Senior AI Program Manager (Operations)  
**Organization:** Bambinos.live  
**Scope:** Re-Engineering & Automating the Student Renewal -> Class Scheduling Pipeline  
**Target Audience:** Head of Operations, Chief Operating Officer, Engineering & Product Leads  
**Document Purpose:** Provide a disciplined, phased execution plan to transition Bambinos from the current manual 4-table workflow to a zero-touch, exception-governed renewal engine supporting 200+ teachers without disrupting live classes.

---

## Executive Overview: Phased Rollout Strategy

A sudden "big-bang" cutover across 200+ teachers and thousands of weekly live classes carries severe operational risks: scheduling dropouts, parent dissatisfaction, and teacher confusion. 

The implementation follows a **3-phase crawl-walk-run methodology**:
* **Phase 1 (Days 0–30): Foundation, Control & Data Standardization** — Fix data integrity, build the prototype dashboard, standardize reason codes, establish baseline SLAs, and run an offline shadow trial.
* **Phase 2 (Days 31–60): Live Automation Pilot (Controlled Cohort)** — Implement webhook triggers, automated matching, and exception triage across a pilot cohort of 25 high-volume teachers (covering ~250 renewals weekly).
* **Phase 3 (Days 61–90): Full Scale Rollout, Hardening & Continuous Optimization** — Scale automation across all 200+ teachers, transition the 10-person Ops team to pure exception management, and lock in the 80%+ auto-approval yield.

```
+---------------------------------------------------------------------------------------------------------+
|                                    30-60-90 DAY IMPLEMENTATION PHASES                                   |
+---------------------------------------------------------------------------------------------------------+
|  DAYS 0–30: FOUNDATION & CONTROL     | DAYS 31–60: AUTOMATION PILOT        | DAYS 61–90: SCALE & OPTIMIZE |
|  - Standardize 10 Reason Codes       | - Deploy n8n webhook ingestion      | - Roll out to all 200+ faculty|
|  - Stand up Ops Head Dashboard       | - Pilot with 25 teachers (250 ren/w)| - Full WhatsApp API slot picker|
|  - Validate Gateway Webhooks         | - Human-in-the-loop exception queues| - Zero overnight backlog SLA |
|  - Offline Shadow Simulation         | - Verify idempotency & zero dups    | - Achieve >= 80% auto-approval|
+---------------------------------------------------------------------------------------------------------+
```

---

## Phase 1: Days 0–30 — Foundation, Control & Data Standardization

### Core Objectives
1. Map, standardize, and audit all data flows and schemas across payments, forms, bookings, and schedules.
2. Formalize operational boundaries: strict financial ground truth, capacity ceilings, and exception ownership.
3. Deploy the prototype Operations Head Daily Dashboard for real-time visibility into queue backlogs.
4. Conduct an offline "Shadow Run" against 100 historical renewals to validate engine accuracy.

### Detailed Weekly Activity Breakdown
* **Week 1: Process Standardization & Data Alignment**
  * Finalize the 10-code reason taxonomy (1 Happy Path + 9 Exception Codes).
  * Formulate data schema definitions for PostgreSQL staging database.
  * Audit payment gateway webhook capabilities (Razorpay / Stripe) for metadata support (`student_id`, `user_id`).
* **Week 2: Governance & Rule Configuration**
  * Establish the Operational SOP v1.0 and review with the 10-person Ops team.
  * Define escalation policies: Manager discount approval threshold (e.g., > 15% requires Ops Head sign-off).
  * Confirm batch capacity ceiling rules (standard 6-student cap with strict atomic lock).
* **Week 3: Dashboard & Shadow Engine Deployment**
  * Deploy Streamlit Executive Dashboard for daily queue tracking and capacity monitoring.
  * Stand up staging environment for `reconciliation_engine.py`.
  * Run retrospective audit across the last 30 days of renewal transactions.
* **Week 4: Faculty Pilot Preparation & Readiness Check**
  * Select 25 pilot teachers (representing diverse courses: Young Communicators, Math, Chess).
  * Conduct 45-minute training workshop for pilot teachers on automated payment link distribution.
  * Establish baseline metrics and execute the Phase 1 Exit Review with the Head of Operations.

### Key Deliverables (Phase 1)
1. Approved Operational Workflow Architecture & SOP v1.0.
2. Standardized Reason-Code Dictionary & Exception Handling Matrix.
3. Live Executive Prototype Dashboard connected to operational staging data.
4. Webhook Feasibility & Technical Dependency Audit Report.
5. Pilot Cohort Roster (25 Teachers) & Readiness Sign-Off.

### Phase 1 Success Metrics & Exit Criteria
* **Engine Accuracy:** >= 99.0% matching accuracy on retrospective shadow trial.
* **Dashboard Reliability:** Daily refresh latency < 60 seconds; zero schema crash errors.
* **Sign-off:** Formal sign-off on SOP and RACI matrix from Head of Operations and Tech Lead.

---

## Phase 2: Days 31–60 — Live Automation Pilot (Controlled Cohort)

### Core Objectives
1. Turn on live webhook-driven automated ingestion for the 25-teacher pilot cohort (~250 renewals/week).
2. Enable zero-touch auto-scheduling for verified happy-path renewals.
3. Route all non-happy path transactions to centralized human-in-the-loop exception queues.
4. Verify database idempotency to ensure zero duplicate calendar bookings or duplicate charges occur.

### Detailed Weekly Activity Breakdown
* **Week 5: Live Pipeline Activation (Pilot Cohort)**
  * Activate payment gateway webhooks routing to n8n workflow engine.
  * Begin automated student roster lookup in reference database upon payment receipt.
  * Enable auto-drafting of WhatsApp confirmations into Ops queue.
* **Week 6: Zero-Touch Scheduling Activation**
  * Enable automated creation of `3_booking_requests` and `4_class_schedule_bookings` for happy-path renewals.
  * Enforce atomic capacity checks (`active_students_count < max_batch_size`).
  * Monitor payment-to-schedule turnaround time (TAT target: < 15 minutes).
* **Week 7: Exception Management & WhatsApp Self-Service**
  * Deploy automated WhatsApp interactive slot picker for parents requesting batch changes.
  * Route partial payments and contact mismatches directly to designated Ops Tier-1/Finance specialists.
  * Integrate Slack `#ops-approvals` for 1-click discount approvals.
* **Week 8: Pilot Evaluation & Stress Testing**
  * Measure pilot auto-approval yield (target: >= 75% for pilot cohort).
  * Conduct mid-implementation audit of error logs and duplicate suppression mechanisms.
  * Interview pilot educators and parents regarding scheduling clarity.

### Key Deliverables (Phase 2)
1. Operational n8n Webhook & Reconciliation Engine in Production Pilot.
2. Active Exception Triage Console in Retool / Streamlit for Ops Team.
3. Interactive WhatsApp Slot Picker Integration (Live Sandbox).
4. Pilot Cohort Performance Audit Report with Measured SLAs.
5. Scale Readiness Checklist for 200+ Teacher Onboarding.

### Phase 2 Success Metrics & Exit Criteria
* **Pilot Auto-Approval Yield:** >= 75.0% of clean pilot renewals scheduled without human touch.
* **Turnaround Time:** Happy-path renewals scheduled in < 15 minutes from payment settlement.
* **Integrity Guarantee:** Exactly **0 duplicate class bookings** and **0 failed payments auto-approved**.
* **Exit Criteria:** Operations Head approval of Pilot Performance Audit.

---

## Phase 3: Days 61–90 — Full Scale Rollout, Hardening & Continuous Optimization

### Core Objectives
1. Expand the automated renewal pipeline to all 200+ active faculty members across India, GCC, and US/UK.
2. Completely phase out manual renewal Google Forms for standard recurring renewals.
3. Re-train and transition the 10-person Operations team into dedicated exception resolution specialists.
4. Establish daily Ops Head review rhythms and institutionalize the continuous optimization backlog.

### Detailed Weekly Activity Breakdown
* **Week 9: Full Faculty Onboarding (Batch 1: 100 Teachers)**
  * Roll out tokenized renewal payment links to first tranche of 100 teachers.
  * Decommission Google Form submissions for happy-path renewals for this cohort.
  * Shift Ops Tier-1 team to monitor live exception triage queues.
* **Week 10: Full Faculty Onboarding (Batch 2: Remaining 75+ Teachers)**
  * Complete full onboarding across all active teachers, including international batches (GCC / US).
  * Activate automated 1-tap WhatsApp confirmation for teachers on edge-case renewals.
  * Establish 24-hour turnaround on custom scholarship discount approvals.
* **Week 11: System Hardening & SLA Enforcement**
  * Conduct end-to-end load testing under peak weekend renewal volume (500+ renewals/day).
  * Enforce strict SLA escalation alerts: P0 (< 15 mins), P1 (< 2 hours), P2 (< 4 hours).
  * Implement automated daily reconciliation report dispatched to Ops Head at 08:00 AM.
* **Week 12: Continuous Improvement & Final Operational Handover**
  * Release Operational SOP v2.0 reflecting live scaled workflows.
  * Finalize Quarterly Ops KPI Review and handover maintenance to internal Data Ops engineer.
  * Establish Q2 product roadmap backlog (e.g., automated batch re-balancing engine).

### Key Deliverables (Phase 3)
1. Complete 200+ Faculty Production Cutover.
2. Operational SOP v2.0 (Scaled Enterprise Edition).
3. Automated Daily Executive Health Digest (Slack / Email).
4. Post-Implementation Performance Review Deck for Leadership.
5. Q2 Continuous Optimization Backlog.

### Phase 3 Success Metrics & Final Target Performance
* **Company-Wide Auto-Approval Yield:** **>= 80.0%** of all renewal volume.
* **Orphaned Invoice Rate:** **0.0%** (< 2 hour automated alert).
* **Payment-to-Schedule TAT:** **< 15 minutes** for clean renewals (down from legacy baseline of 104.7 mins).
* **Pending Backlog:** **Zero overnight backlog** (all paid renewals scheduled within the business day).
* **Ops Efficiency:** 10-person Ops team successfully supports 200+ teachers with **< 2 hours spent per executive daily on data verification**.

---

## Summary of Implementation Risks & Mitigation Strategies

```
+--------------------------------------------------------------------------------------------------------------------+
| Identified Risk               | Likelihood | Impact | Mitigation Strategy                                | Owner   |
+--------------------------------------------------------------------------------------------------------------------+
| 1. Teacher Pushback / Form     | Medium     | High   | Frame as administrative relief ("we took data entry| Ops Lead|
|    Habit                      |            |        | off your plate"); incentivize via prompt roster view|         |
| 2. Payer Phone Discrepancies  | High       | Medium | Tokenize payment links with student_id; secondary  | Product |
|                               |            |        | family contact lookup in user master profile.      |         |
| 3. Batch Capacity Sockets     | Medium     | High   | Atomic database check-and-lock queries; automated  | Systems |
|                               |            |        | sister batch reservation 7 days before term end.   | Specialist|
| 4. Payment Gateway Webhook Lag| Low        | High   | Implement fallback polling worker running every 15 | Systems |
|                               |            |        | minutes for missed webhook events.                 | Specialist|
+--------------------------------------------------------------------------------------------------------------------+
```
