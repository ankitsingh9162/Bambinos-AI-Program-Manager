# Re-Engineered Workflow Architecture: The 'Zero-Touch' Renewal Engine (Validated)

**Role:** AI Program Manager (Operations)  
**Organization:** Bambinos.live  
**Scope:** Re-Engineering & Automating the Student Renewal -> Class Scheduling Pipeline  
**Dataset Base:** `./ops/data/` (5 Production Datasets & Deliverable A Findings)  
**Companion Documents:**
- [`exception_handling_matrix.csv`](file:///c:/Users/hp/Downloads/mongodb%20project/AI-PM-hiring-take-home-assignments/ops/audit/exception_handling_matrix.csv) (10 Standardized Reason Codes)
- [`workflow_diagram.mmd`](file:///c:/Users/hp/Downloads/mongodb%20project/AI-PM-hiring-take-home-assignments/ops/audit/workflow_diagram.mmd) (Mermaid Diagram)
- [`automation_safeguards.md`](file:///c:/Users/hp/Downloads/mongodb%20project/AI-PM-hiring-take-home-assignments/ops/audit/automation_safeguards.md) (Governance & Safeguards)
- [`operational_kpis.md`](file:///c:/Users/hp/Downloads/mongodb%20project/AI-PM-hiring-take-home-assignments/ops/audit/operational_kpis.md) (Metric Formulas & SLAs)

---

## 1. Context, Facts, Recommendations, and Assumptions

To maintain complete analytical transparency, this architecture separates **empirical facts**, **proposed recommendations**, and **implementation dependencies/assumptions**:

### 1.1 Empirical Facts (Supported by Provided CSVs)
1. Moving a student from payment to class scheduling involves 4 sequential tables: `1_invoices.csv` -> `2_faculty_form_unapproved.csv` -> `3_booking_requests.csv` -> `4_class_schedule_bookings.csv`.
2. Across the cohort of 13 invoices, exactly **1 unique student (`68101`)** reached final class scheduling, taking **104.7 minutes** of elapsed time across multiple manual handoffs.
3. Out of 11 successfully paid invoices, **2 invoices (`84906` and `84910`)** were never submitted by any teacher (**18.2% Orphaned Paid Invoices**), leaving INR 29,000 in renewal fees in scheduling limbo.
4. Technical and human errors in the data include:
   - Form duplicate submission from browser freeze (Forms `3308` & `3309`).
   - Teacher typo in invoice ID (Form `3313` entered `84931` instead of `84913`).
   - Payment status mismatches (Form `3310` partial payment; Form `3311` failed payment).
   - Batch overcapacity (Booking `5505` failed because Batch `9205` was at 6/6 capacity).

### 1.2 Proposed Recommendations (Operational Redesign)
1. Invert the renewal trigger: Use payment gateway webhooks as the primary event to initiate renewals, eliminating teacher form entry as a prerequisite bottleneck.
2. Establish a **Zero-Touch Fast-Track** for clean, recurring renewals (same batch, verified payment, available capacity).
3. Implement a standardized 10-code exception matrix (1 Happy Path + 9 Exception Codes) for automated triage.
4. Adopt self-hosted `n8n` as the primary workflow engine, PostgreSQL for ACID-compliant state storage, and WhatsApp Business API for parent self-service.

### 1.3 Key Implementation Dependencies & Assumptions (Requiring Leadership Confirmation)
1. **Payment Gateway Webhook Availability (Assumption):** Assumes the payment gateway (Razorpay / Stripe) can be configured to emit real-time webhook payloads on `payment.captured` and `payment.failed`.
2. **Student & Parent Tokenization (Assumption):** Assumes payment links pitched to parents can include tokenized query parameters (`student_id`, `user_id`), enabling reliable matching even if the payer's phone number differs.
3. **Session Cycle Standard (Assumption):** In the provided dataset, standard packages are recorded as `standard_fee_24_sessions_inr = 24 sessions`. Assumes 24 sessions is the standard term renewal cycle across courses.
4. **Batch Capacity Ceiling (Dataset Example):** In `reference_active_batches_and_students.csv`, all batches have `max_batch_size = 6`. This is treated as a **dataset-observed capacity ceiling** rather than a company-wide universal policy, pending operational confirmation.
5. **WhatsApp & Slack Integration (Assumption):** Assumes Bambinos has access to the Meta WhatsApp Business Cloud API (via BSPs like WATI or Gupshup) for interactive messages, and Slack API for Ops team escalations.
6. **Infrastructure Transition (Assumption):** Assumes an architectural migration from disconnected spreadsheets to an ACID-compliant relational store (PostgreSQL / Supabase) to guarantee atomic batch capacity reservation.

---

## 2. End-to-End Workflow Mapping (Step-by-Step)

```
+----------------------------------------------------------------------------------------------------------------------------------+
|                                    END-TO-END RENEWAL WORKFLOW STAGES                                                            |
+----------------------------------------------------------------------------------------------------------------------------------+
| Step 1: Payment Ingestion (Automated)                                                                                            |
|         Gateway webhook (Razorpay/Stripe) captures payment event -> Ingests into `1_invoices.csv` -> Resolves `payment_status`.   |
|                                                                                                                                  |
| Step 2: Automated Entity Lookup & Inversion (Automated)                                                                          |
|         System queries `reference_active_batches_and_students` by `student_id`/`user_id` -> Retrieves active batch ID, educator, |
|         and capacity. Teacher form is NO LONGER a prerequisite gatekeeper.                                                       |
|                                                                                                                                  |
| Step 3: Integrity & Discrepancy Evaluation (Automated)                                                                           |
|         System executes deterministic rule matrix: checks amount, phone match, batch capacity, duplicate status, and discounts.   |
|                                                                                                                                  |
| Step 4: Branching Decision Gate                                                                                                  |
|         [BRANCH A: Happy Path (Automated)] -> If all 5 criteria pass, proceed to Step 5 immediately.                            |
|         [BRANCH B: Exception Triage (Automated Routing / Human Resolution)] -> Trigger standardized reason code, alert exact    |
|         owner (Ops, Parent, Teacher), and route to Live Dashboard / WhatsApp.                                                   |
|                                                                                                                                  |
| Step 5: Booking Request & Batch Locking (Automated)                                                                              |
|         Atomic capacity check on `current_classbatch_id` -> Insert `3_booking_requests` (`status = 'Completed'`).                |
|                                                                                                                                  |
| Step 6: Live Class Scheduling (Automated)                                                                                        |
|         Generate 24 term session records in `4_class_schedule_bookings` -> Increment batch student count.                        |
|                                                                                                                                  |
| Step 7: Omnichannel Parent & Teacher Notification (Automated)                                                                    |
|         Parent receives WhatsApp confirmation with calendar invites -> Teacher receives portal notification of renewed student.  |
+----------------------------------------------------------------------------------------------------------------------------------+
```

---

## 3. The Happy-Path Zero-Touch Workflow

The "Happy Path" represents recurring renewals that satisfy all 5 deterministic validation criteria:
1. **Full Payment Confirmed:** `invoices.payment_status == 'Paid'` AND `net_amount == standard_fee_24_sessions_inr`.
2. **Student & Parent Verified:** `student_id` matches active roster; payer phone/email matches registered profile.
3. **Same Batch & Teacher Requested:** `continue_same_batch == 'Yes'`.
4. **Batch Capacity Available:** `active_students_count < max_batch_size` (e.g., `< 6`).
5. **No Special Discretionary Discount:** `discount_amount == 0` (or pre-authorized standard coupon).

### Proposed Performance Targets (Subject to Implementation Testing):
* **Human Touchpoints Required:** **Zero**.
* **Proposed Target Turnaround Time:** **< 5 minutes** (compared to observed baseline of 104.7 minutes for Student `68101`).
* **Proposed Auto-Approval Yield Target:** **>= 80%** of total renewal volume.
* **Empirical Feasibility in Sample Dataset:** In our 13-student cohort, Students `68101`, `68102`, and `68103` meet these clean criteria. While `68101` was eventually scheduled after 104.7 minutes, `68102` remains stuck in Ops batch allocation and `68103` remains stuck in unapproved review. Under this zero-touch engine, both would have been automatically scheduled.

---

## 4. Standardized 10-Code Reason Matrix (1 Happy Path + 9 Exceptions)

Every transaction entering the pipeline is classified into one of **10 standardized Reason Codes** (1 Happy-Path Code and 9 Exception Codes). *(Full schema available in [`exception_handling_matrix.csv`](file:///c:/Users/hp/Downloads/mongodb%20project/AI-PM-hiring-take-home-assignments/ops/audit/exception_handling_matrix.csv))*.

```
+---------------------------------------------------------------------------------------------------------------+
| Reason Code                   | Category      | Detection Condition                     | Proposed Target SLA |
+---------------------------------------------------------------------------------------------------------------+
| 1. HAPPY_PATH_AUTO_APPROVED   | Happy-Path    | Full payment + Same batch + Capacity ok | < 5 minutes         |
| 2. FACULTY_FORM_MISSING       | Omission      | Paid invoice, no form after 2 hours     | < 2 hours           |
| 3. PHONE_MISMATCH             | Discrepancy   | Payer phone != student master phone     | < 2 hours           |
| 4. PARTIAL_PAYMENT            | Financial     | Net paid amount < standard term fee     | < 4 hours           |
| 5. PAYMENT_FAILED             | Financial     | Gateway status == 'Failed'              | < 15 minutes        |
| 6. INVOICE_ID_MISMATCH        | Discrepancy   | Form invoice_id not in invoices table   | < 30 minutes        |
| 7. DUPLICATE_FORM             | Technical     | Multiple forms for same student/invoice | < 5 minutes         |
| 8. BATCH_FULL                 | Capacity      | Active count >= max batch size (e.g. 6) | < 3 hours           |
| 9. BATCH_CHANGE_REQUIRED      | Scheduling    | Parent requested day/time slot change   | < 4 hours           |
| 10. SCHOLARSHIP_APPROVAL_REQ  | Authorization | Discount applied requiring Ops sign-off | < 2 hours           |
+---------------------------------------------------------------------------------------------------------------+
```

### Detailed Breakdown of the 9 Exception Codes:

1. **`FACULTY_FORM_MISSING` (Omission Exception)**
   - *Detection Condition:* `invoices.payment_status == 'Paid'` AND `paid_at < NOW() - 2 hours` AND NOT EXISTS in `faculty_form_unapproved`.
   - *Automated Action:* System auto-fetches student record from reference table; initiates renewal workflow; dispatches 1-tap WhatsApp prompt to teacher.
   - *Designated Owner:* Ops Tier 1 / Assigned Teacher.
   - *Notification Action:* Parent received WhatsApp W2 ("Payment received, scheduling your class"); Teacher receives Alert T2 ("1-click confirm renewal").
   - *Proposed SLA Target:* < 2 hours.

2. **`PHONE_MISMATCH` (Data Discrepancy Exception)**
   - *Detection Condition:* `invoices.mobile != reference.registered_mobile` AND `email != reference.registered_email`.
   - *Automated Action:* Check secondary family profile contacts via `user_id`. If unresolved, route to Ops exception queue.
   - *Designated Owner:* Ops Tier 1 (Verification Agent).
   - *Notification Action:* Parent receives WhatsApp W3 ("Payment received from new contact; please confirm child name").
   - *Proposed SLA Target:* < 2 hours.

3. **`PARTIAL_PAYMENT` (Financial Exception)**
   - *Detection Condition:* `invoices.payment_status == 'Partially_Paid'` OR `invoices.net_amount < standard_fee_24_sessions_inr`.
   - *Automated Action:* Hold scheduling; calculate outstanding balance; generate dynamic payment link for remaining tranche.
   - *Designated Owner:* Finance / Retention Lead.
   - *Notification Action:* Parent receives WhatsApp W4 ("Partial fee received; tap here to pay balance"); Teacher receives Alert T3 ("Partial payment noted").
   - *Proposed SLA Target:* < 4 hours.

4. **`PAYMENT_FAILED` (Financial Exception)**
   - *Detection Condition:* `invoices.payment_status == 'Failed'` OR form submitted without settled gateway payment ID.
   - *Automated Action:* Reject unverified submission; block scheduling; log alert; generate secure payment retry link.
   - *Designated Owner:* Automated Gateway Triage / Ops Tier 1.
   - *Notification Action:* Parent receives WhatsApp W5 ("Payment unsuccessful; tap to retry"); Teacher receives Alert T4 ("UPI payment failed; do not start classes").
   - *Proposed SLA Target:* < 15 minutes.

5. **`INVOICE_ID_MISMATCH` (Data Discrepancy Exception)**
   - *Detection Condition:* `faculty_form.invoice_id NOT IN invoices.id`.
   - *Automated Action:* Fuzzy reconcile on `faculty_form.student_id == invoices.student_id` where `payment_status == 'Paid'`. Auto-correct if single unambiguous match; flag to Ops if ambiguous.
   - *Designated Owner:* Automated Reconciliation Engine (Ops fallback).
   - *Notification Action:* Teacher receives Alert T5 ("Invoice ID typo auto-corrected").
   - *Proposed SLA Target:* < 30 minutes.

6. **`DUPLICATE_FORM` (Technical Discrepancy Exception)**
   - *Detection Condition:* Multiple rows with identical `(student_id, invoice_id)` in faculty submissions.
   - *Automated Action:* Retain first valid submission; flag subsequent rows as `DUPLICATE_SUPPRESSED`; prevent duplicate booking requests.
   - *Designated Owner:* Automated Engine.
   - *Notification Action:* Teacher receives Alert T6 ("Duplicate submission detected and merged").
   - *Proposed SLA Target:* < 5 minutes.

7. **`BATCH_FULL` (Capacity Exception)**
   - *Detection Condition:* `continue_same_batch == 'Yes'` AND `reference.active_students_count >= reference.max_batch_size`.
   - *Automated Action:* Flag as `BATCH_FULL`; query database for sister batches at same grade/curriculum; draft batch alternatives.
   - *Designated Owner:* Academic Ops Lead / Batch Scheduler.
   - *Notification Action:* Parent receives WhatsApp W6 ("Batch is at full capacity; here are 2 sister batches with open slots"); Teacher receives Alert T7.
   - *Proposed SLA Target:* < 3 hours.

8. **`BATCH_CHANGE_REQUIRED` (Scheduling Exception)**
   - *Detection Condition:* Parent requested new time/day slot (`continue_same_batch == 'No'`).
   - *Automated Action:* Hold booking request in `Awaiting_Parent_Batch_Selection`; dispatch interactive WhatsApp slot picker widget showing live open slots.
   - *Designated Owner:* Parent Self-Service (Ops Tier 1 fallback after 12h).
   - *Notification Action:* Parent receives Interactive WhatsApp W7 ("Select your child's new preferred days and time slot"); Teacher receives Alert T8.
   - *Proposed SLA Target:* < 4 hours.

9. **`SCHOLARSHIP_APPROVAL_REQUIRED` (Authorization Exception)**
   - *Detection Condition:* `invoices.discount_amount > 0` OR faculty form remarks indicate retention scholarship.
   - *Automated Action:* Verify discount percentage against retention policy; route approval card to Slack `#ops-approvals` with `[Approve]` / `[Reject]` buttons.
   - *Designated Owner:* Head of Operations / Retention Lead.
   - *Notification Action:* Parent receives WhatsApp W8 ("Scholarship renewal processing"); Manager receives Slack Alert with 1-click button.
   - *Proposed SLA Target:* < 2 hours.

---

## 5. Technology Stack Architecture & Rationale

```
+-------------------------------------------------------------------------------------------------------------+
|                                    PROPOSED NO-CODE & AI TOOL STACK                                         |
+-------------------------------------------------------------------------------------------------------------+
| Component              | Recommended Tool          | Operational Role & Rationale                           |
+-------------------------------------------------------------------------------------------------------------+
| 1. Workflow Engine     | n8n (Self-hosted) / Make  | Orchestrates webhooks, executes deterministic logic,   |
|                        |                           | and manages branching loops without per-task cost spike|
| 2. Master Relational DB| PostgreSQL / Supabase     | Provides ACID transactions and atomic capacity locking |
|                        |                           | (`active_count < max_size`) to prevent race conditions.|
| 3. Operational UI      | Metabase / Retool         | Live Ops queue monitor, exception triage, and 1-click   |
|                        |                           | manual override console for 10-person Ops team.        |
| 4. AI & Parsing Layer  | Claude 3.5 Sonnet /       | Semantic extraction of unstructured teacher remarks    |
|                        | GPT-4o-mini (LLM)         | and contextual message drafting. ZERO financial power. |
| 5. Messaging Gateway   | WhatsApp Cloud API        | Interactive slot picker, automated payment retry links,|
|                        | (via WATI / Gupshup)      | and calendar confirmations for parents and teachers.   |
| 6. Escalation Triage   | Slack API                 | Instant manager alerts for Level 3/4 exceptions and    |
|                        |                           | 1-click scholarship discount sign-off cards.           |
+-------------------------------------------------------------------------------------------------------------+
```

---

## 6. Measurable SLA Commitments: Baseline vs. Proposed Targets

All targets are clearly designated as **proposed operational SLA targets** for post-implementation benchmarking:

| Operational Metric | Deliverable A Empirical Baseline | Proposed Operational Target | Core Mechanism to Achieve Target |
| :--- | :---: | :---: | :--- |
| **Orphaned Invoice Rate** | **18.2%** (2 of 11 Paid) | **0.0%** (< 2h alert) | Webhook ingestion eliminates teacher as prerequisite |
| **Payment-to-Schedule TAT** | **104.7 mins** (Single student) | **< 15 mins** (Happy Path) | Zero-touch auto-scheduling of clean renewals |
| **Form Submission Delay** | **27.8 mins avg** | **0 mins** (Bypassed) | Reference database auto-populates student roster |
| **Auto-Approval Rate** | **0.0%** (100% manual) | **>= 80.0%** | Standard recurring renewals bypass Ops review queue |
| **Operational Exception Rate** | **53.8%** (7 of 13 Cohort) | **< 10.0%** | Frontend validation, tokenized links, and dropdowns |
| **Pending Renewal Backlog** | **11 students** | **0 overnight backlog** | Same-day resolution through tiered escalation queues |

---

## 7. Workflow Diagram Verification

The visual flow documented in [`workflow_diagram.mmd`](file:///c:/Users/hp/Downloads/mongodb%20project/AI-PM-hiring-take-home-assignments/ops/audit/workflow_diagram.mmd) aligns with the architecture:
- Stage 1: Ingestion & Financial Verification (`PAYMENT_FAILED`, `PARTIAL_PAYMENT`).
- Stage 2: Roster Integrity & Form Matching (`FACULTY_FORM_MISSING`, `DUPLICATE_FORM`, `INVOICE_ID_MISMATCH`, `PHONE_MISMATCH`, `SCHOLARSHIP_APPROVAL_REQUIRED`).
- Stage 3: Capacity & Slot Selection (`BATCH_FULL`, `BATCH_CHANGE_REQUIRED`, `HAPPY_PATH_AUTO_APPROVED`).
- Stage 4: Scheduling & Notification (Class booking and WhatsApp/Slack alerts).
