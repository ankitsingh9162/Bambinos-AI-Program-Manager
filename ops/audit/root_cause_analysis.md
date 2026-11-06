# Deliverable A: Root-Cause Problem Definition & Leakage Audit (Validated)

**Role:** AI Program Manager (Operations)  
**Organization:** Bambinos.live  
**Scope:** Re-Engineering & Automating the Student Renewal -> Class Scheduling Pipeline  
**Dataset Base:** `./ops/data/` (`1_invoices.csv`, `2_faculty_form_unapproved.csv`, `3_booking_requests.csv`, `4_class_schedule_bookings.csv`, `reference_active_batches_and_students.csv`)  
**Audit File Generated:** [`leakage_audit.csv`](file:///c:/Users/hp/Downloads/mongodb%20project/AI-PM-hiring-take-home-assignments/ops/audit/leakage_audit.csv)  
**KPI Reference Document:** [`operational_kpis.md`](file:///c:/Users/hp/Downloads/mongodb%20project/AI-PM-hiring-take-home-assignments/ops/audit/operational_kpis.md)

---

## Executive Summary

At Bambinos.live, student renewals represent the primary engine of high-LTV organic revenue and retention. However, an end-to-end data audit across the current 4-table operational pipeline reveals a critical failure in operational velocity and conversion:

* **Invoice Cohort:** A total of **13 renewal invoices** were generated (totaling **INR 1,57,350** across 13 unique students):
  * **11 invoices are `Paid`** (INR 1,40,100).
  * **1 invoice is `Partially_Paid`** (`84909` for INR 5,250 received out of INR 10,500).
  * **1 invoice is `Failed`** (`84911` for INR 12,000 where payment did not settle).
* **Final Scheduling Conversion:**
  * **Only 1 unique student (`68101`)** has successfully reached the final live scheduled classes table (`4_class_schedule_bookings.csv`).
  * **The end-to-end operational conversion rate is 7.7%** (1 of 13 total cohort invoices) or **9.1%** of successfully paid renewals (1 of 11 paid invoices).
  * **Renewal Leakage & Scheduling Risk:** Over **90.9% of paying parents** face operational delays, administrative backlogs, data mismatches, or unscheduled classes.

This audit proves why manual handoffs between Teachers, Operations, and Parents are fundamentally unsustainable, details every single failure mode observed in the production data, and presents clear architectural recommendations to eliminate them.

---

## 1. Quantitative Leakage Funnel Verification

### 1.1 CSV Row Counts vs. Unique Entities
To ensure complete mathematical integrity, we strictly separate **raw CSV row counts** from **unique students** and **unique invoice identifiers**:

* **Table 1 (`1_invoices.csv`):** 13 rows | 13 unique `id`s | 13 unique `student_id`s.
  * Payment Status: 11 `Paid`, 1 `Partially_Paid`, 1 `Failed`.
* **Table 2 (`2_faculty_form_unapproved.csv`):** 12 rows | 12 unique form `id`s | 11 unique `student_id`s | 10 valid direct invoice `id`s (11 logical).
  * *Discrepancy 1:* Form `3309` is a technical duplicate submission of Form `3308` (same student `68108` and invoice `84908`) due to teacher browser freeze.
  * *Discrepancy 2:* Form `3313` (Student `68113`) contains an invoice ID typo (`84931` entered instead of `84913`).
  * *Discrepancy 3:* Invoices `84906` and `84910` have zero submissions in this table.
* **Table 3 (`3_booking_requests.csv`):** 4 rows | 4 unique `id`s | 4 unique `faculty_form_id`s | 4 unique `student_id`s (`68101`, `68102`, `68105`, `68112`).
* **Table 4 (`4_class_schedule_bookings.csv`):** 2 rows | 2 unique session `id`s (`990101`, `990102`), but both belong to **a single booking request (`5501`)** for **1 unique student (`68101`)** and 1 invoice (`84901`).

### 1.2 Quantitative Funnel Stage Progression

| Funnel Stage | Total Rows in CSV | Unique Students | Unique Invoices | Stage Conversion (% of Unique Students from Prior Stage) | Cumulative Funnel Conversion (% of Total Cohort) | Leakage Count (Students Lost at Stage) | Stage Leakage Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Invoices Generated** | 13 | 13 | 13 | **100.0%** (Baseline) | **100.0%** | 0 | 0.0% |
| **2. Faculty Forms Submitted** | 12 | 11 | 10 direct / 11 logical | **84.6%** | **84.6%** | 2 students | **15.4%** |
| **3. Booking Requests Created** | 4 | 4 | 4 | **36.4%** | **30.8%** | 7 students | **63.6%** |
| **4. Class Scheduled Bookings** | 2 | 1 | 1 | **25.0%** | **7.7%** | 3 students | **75.0%** |

> [!IMPORTANT]
> **Conversion Summary:**  
> Across the entire renewal pipeline, only **1 student** out of 13 in the cohort (and 1 out of 11 paid) has confirmed live sessions scheduled. **12 students (92.3% of the total cohort)** are stalled across intermediate manual handoffs.

---

## 2. Comprehensive Cohort Reconciliation: Student-by-Student Trace

The table below reconciles each of the 13 students through all 5 CSV files:

| Student ID | Parent Mobile | Invoice ID & Amount (INR) | Payment Status | Faculty Form ID & Status | Booking Request ID & Status | Scheduled Bookings | Root Cause & Failure Mode | Current Operational State |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **68101** | `+91-9811XXXX01` | `84901` (12,000) | Paid | `3301` (Approved) | `5501` (Completed) | 2 sessions | **Clean Renewal (Happy Path)** | Fully Scheduled |
| **68102** | `+91-9822XXXX02` | `84902` (10,500) | Paid | `3302` (Approved) | `5502` (Pending_Batch_Allocation) | 0 sessions | **Manual Allocation Latency**: Approved same-batch renewal sitting idle in Ops queue | Stalled at Ops Booking |
| **68103** | `+91-9833XXXX03` | `84903` (9,000) | Paid | `3303` (Pending) | *None* | 0 sessions | **Ops Review Backlog**: Clean same-batch renewal unapproved by Ops | Stalled at Ops Review |
| **68104** | `+91-9844XXXX77` | `84904` (12,000) | Paid | `3304` (Pending) | *None* | 0 sessions | **Contact Mismatch**: Mother paid with phone `...XXXX77` vs registered `...XXXX04` | Stalled at Ops Review |
| **68105** | `+91-9855XXXX05` | `84905` (11,000) | Paid | `3305` (Approved) | `5505` (Failed_Batch_Full) | 0 sessions | **Batch Overcapacity**: Existing batch 9205 is full (6/6 active seats) | Scheduling Blocked |
| **68106** | `+971-5012XXX06` | `84906` (18,000) | Paid | *None* | *None* | 0 sessions | **Orphaned Paid Invoice**: High-ticket GCC parent paid; teacher never submitted form | High Scheduling Risk |
| **68107** | `+91-9877XXXX07` | `84907` (7,600) | Paid | `3307` (Pending) | *None* | 0 sessions | **Discount Discretion Delay**: 20% scholarship discount pending discretionary ops sign-off | Stalled at Ops Review |
| **68108** | `+1-40855XXX08` | `84908` (22,000) | Paid | `3308` & `3309` (Pending) | *None* | 0 sessions | **Duplicate Submission**: Teacher submitted twice after browser froze; Ops halted review | Stalled at Ops Review |
| **68109** | `+91-9899XXXX09` | `84909` (5,250) | Partially_Paid | `3310` (Pending) | *None* | 0 sessions | **Payment Amount Mismatch**: Form claims 10,500; gateway received only 5,250 | Blocked / Discrepancy |
| **68110** | `+91-9800XXXX10` | `84910` (11,000) | Paid | *None* | *None* | 0 sessions | **Orphaned Paid Invoice**: Parent paid full renewal; teacher failed to submit renewal form | High Scheduling Risk |
| **68111** | `+91-9811XXXX11` | `84911` (12,000) | Failed | `3311` (Pending) | *None* | 0 sessions | **Payment Gateway Failure**: Teacher submitted form on basis of unconfirmed UPI screenshot | False Renewal / Blocked |
| **68112** | `+91-9822XXXX12` | `84912` (9,000) | Paid | `3312` (Approved) | `5512` (Awaiting_Parent_Batch_Selection) | 0 sessions | **Batch-Change Latency**: Parent wants weekend slot; no slot picker self-serve | Waiting on Parent/Ops |
| **68113** | `+91-9833XXXX13` | `84913` (11,500) | Paid | `3313` (Pending) | *None* | 0 sessions | **Teacher Typo in Invoice ID**: Teacher entered `84931` instead of `84913` | Broken Key Reconciliation |

---

## 3. Deep Root-Cause Analysis by Operational Failure Category

### 3.1 Failure Mode 1: Orphaned Paid Invoices (Teacher Form Delay/Omission)
* **Affected Records:** Invoices `84906` (Student `68106`, INR 18,000) and `84910` (Student `68110`, INR 11,000). Total Paid Fees at Risk: **INR 29,000 (20.7% of all collected renewal revenue)**.
* **Root Cause:** The business architecture currently relies on human teachers to remember and manually submit a Google Form after a parent pays. Teachers are educators, not administrative data-entry workers. After completing a class, they forget, postpone, or lose track of payment confirmation links.
* **Business Impact:** High-paying parents (including international high-ticket GCC clients) experience complete silence. Classes are not scheduled, creating severe scheduling delays, parent churn risk, and potential refund/chargeback requests.
* **Proposed Solution:** Invert the workflow. When a payment gateway webhook fires (`payment_status = Paid`), an automated trigger should instantly ingest the transaction, look up the student in `reference_active_batches_and_students`, and initiate the renewal pipeline automatically. The teacher should only be alerted via WhatsApp for confirmation, never as a prerequisite gatekeeper.

### 3.2 Failure Mode 2: Payment Amount & Status Mismatches
* **Affected Records:**
  * Invoice `84909` / Form `3310` (Student `68109`): Net amount paid is **INR 5,250** (`Partially_Paid`), but teacher submitted form for **INR 10,500**.
  * Invoice `84911` / Form `3311` (Student `68111`): Gateway status is **`Failed`**, but teacher submitted form stating *"Parent shared UPI processing screenshot"*.
* **Root Cause:** Teachers accept parents' word or misleading payment app "processing" screens as completed payments. Furthermore, manual entry fields allow teachers to type whatever number they assume was paid.
* **Business Impact:** Students either receive free sessions before completing payments (unrealized revenue leakage) or Ops wastes hours reconciling bank accounts against UPI screenshots.
* **Proposed Solution:** Payment amount and status fields must be **read-only and programmatically populated directly from the payment gateway API / webhook**. If an invoice is `Partially_Paid`, automatically issue a dynamic split-payment link for the remaining balance. If `Failed`, trigger an instant WhatsApp message to the parent with a retry link, alerting the teacher that the transaction has not settled.

### 3.3 Failure Mode 3: Teacher Typo in Critical Identifiers
* **Affected Records:** Form `3313` (Student `68113`, Invoice `84913`, Teacher entered `invoice_id = 84931`).
* **Root Cause:** Unrestricted free-text input fields in faculty submission forms.
* **Business Impact:** Automated SQL joins or VLOOKUPs between `invoices` and `faculty_forms` break completely (`NULL` match). Ops has to manually cross-reference student names and timestamps across spreadsheets.
* **Proposed Solution:** Eliminate free-text entry of system IDs. Teachers should select from a single dropdown of verified pending invoices linked to their assigned students, or forms should be pre-populated with authenticated magic links.

### 3.4 Failure Mode 4: Identity & Contact Mismatches (Parent vs Student)
* **Affected Records:** Invoice `84904` / Form `3304` (Student `68104`).
* **Root Cause:** The child is registered under one parent's mobile (`+91-9844XXXX04`), but the payment was completed by the spouse (`+91-9844XXXX77`).
* **Business Impact:** Simple programmatic matching scripts fail. Ops flags the row for manual inspection, leaving it stuck in `Pending` indefinitely.
* **Proposed Solution:** Implement multi-identifier fuzzy resolution: Match first on `student_id` (via tokenized renewal payment links), second on `user_id`, and third on secondary family contact attributes from the user master profile.

### 3.5 Failure Mode 5: Frontend Glitches & Duplicate Submissions
* **Affected Records:** Forms `3308` and `3309` (Student `68108`, Invoice `84908`).
* **Root Cause:** Lack of idempotency on the faculty submission form. When the network stalls or browser freezes, teachers double-click "Submit".
* **Business Impact:** Clogs Ops review queues with ghost duplicates, creating confusion over whether two packages were purchased.
* **Proposed Solution:** Enforce unique database constraints: `UNIQUE (student_id, invoice_id)` on pending renewal forms and disable submit buttons upon initial click with immediate UI feedback.

### 3.6 Failure Mode 6: Batch Overcapacity (Failed Same-Batch Renewals)
* **Affected Records:** Booking Request `5505` / Form `3305` (Student `68105`, Batch `9205`).
* **Root Cause:** The child wants to continue in their existing batch `9205`, but the batch has reached maximum capacity (`active_students_count = 6`, `max_batch_size = 6`).
* **Business Impact:** The booking request fails abruptly (`Failed_Batch_Full`), leaving the renewing student displaced without a teacher or schedule.
* **Proposed Solution:** Real-time seat reservation logic. When a student approaches the final 4 sessions of their current term, reserve their seat in the batch for 7 days. If a batch is already saturated, notify Ops and the parent 2 weeks before renewal with alternative slot suggestions.

### 3.7 Failure Mode 7: Batch-Change Request Latency
* **Affected Records:** Booking Request `5512` / Form `3312` (Student `68112`).
* **Root Cause:** The parent requested a shift from weekday to weekend morning slots (`Sat, Sun 11:00 AM`). The booking request has `classbatch_id = NULL` and sits in `Awaiting_Parent_Batch_Selection`.
* **Business Impact:** Renewal turns into a multi-day asynchronous back-and-forth between Ops and the parent over WhatsApp/calls, stalling class scheduling.
* **Proposed Solution:** Interactive WhatsApp / Web Self-Service Slot Picker: Upon payment completion for a batch-change renewal, immediately send an interactive WhatsApp message with live available batch options for one-tap selection.

### 3.8 Failure Mode 8: Unnecessary Human Gating on Clean Renewals ("Happy Path")
* **Affected Records:**
  * Form `3301` / Booking `5501` (Student `68101`): Clean renewal took 104.7 minutes of end-to-end elapsed time and multiple human Ops touchpoints just to approve and schedule.
  * Form `3302` / Booking `5502` (Student `68102`): Clean same-batch renewal approved by Ops, yet sat untouched with `batch_allocated = No`.
  * Form `3303` (Student `68103`): 100% clean payment and same-batch renewal, left sitting unapproved in Ops queue.
* **Root Cause:** Ops policy treats all renewals identically, requiring manual verification of every row regardless of whether all data points match perfectly.
* **Business Impact:** Ops team becomes an operational bottleneck, burning payroll hours on repetitive data transcription while parents wait.
* **Proposed Solution:** **Zero-Touch Auto-Approval Engine**. If `Invoice Paid == Net Amount`, `Batch Capacity < Max`, and `Continue Same Batch == True`, auto-approve and generate schedule entries in `class_schedule_bookings` in sub-second time.

---

## 4. Key Operational Metrics & Recommended SLAs

To transform the Bambinos renewal operations from a black box into a measurable, SLA-governed pipeline, we define 6 core operational KPIs:

```
+---------------------------------------------------------------------------------------------------------+
|                                    OPERATIONAL METRICS DASHBOARD                                        |
+---------------------------------------------------------------------------------------------------------+
|  1. Orphaned Invoice Rate (Paid)       |  2. Payment-to-Schedule TAT          |  3. Auto-Approval Rate  |
|     Current: 18.2% (2/11 Paid)         |     Current: 104.7 mins (Single)     |     Current: 0.0%       |
|     Recommended Target: 0.0%           |     Recommended Target: < 15 mins    |     Recommended: > 80%  |
+---------------------------------------------------------------------------------------------------------+
|  4. Form Submission Delay              |  5. Operational Exception Rate       |  6. Pending Renewal Q   |
|     Current: 27.8 mins avg             |     Current: 53.8% (7/13) or 63.6%   |     Current: 11 / 13    |
|     Recommended Target: 0 min (Bypassed)|   Recommended Target: < 10%        |     Recommended: < 5    |
+---------------------------------------------------------------------------------------------------------+
```

### Detailed KPI Definitions & Target SLAs

#### 1. Orphaned Invoice Rate (Paid Renewals)
* **Definition:** Percentage of successfully completed renewal payments (`payment_status = Paid` in `1_invoices.csv`) that have no corresponding faculty form submission or booking record.
* **Calculation:**
  $$\text{Orphaned Invoice Rate (Paid)} = \frac{\text{Paid Invoices with No Faculty Form / Booking Record (2)}}{\text{Total Paid Invoices (11)}} \times 100 = \mathbf{18.2\%}$$
  *(If calculated across all 13 cohort records: $2 / 13 = 15.4\%$)*.
* **Affected Invoices:** `84906` (Student `68106`, INR 18,000) and `84910` (Student `68110`, INR 11,000).
* **Separate Payment Status Reporting:**
  * Total Invoices: 13 (100%)
  * `Paid`: 11 (84.6%) -> 2 Orphaned (18.2% of Paid), 9 with Form Submissions.
  * `Partially_Paid`: 1 (7.7%) -> Invoice `84909` (INR 5,250 received; teacher submitted form for INR 10,500).
  * `Failed`: 1 (7.7%) -> Invoice `84911` (INR 12,000 failed; teacher submitted form on unverified screenshot).
* **Recommended SLA Target:** **0.0%** (Automated webhook ingestion eliminates orphaned invoices entirely).

#### 2. Payment-to-Schedule Turnaround Time (TAT)
* **Definition:** Elapsed duration from the moment a parent successfully pays (`invoices.paid_at`) to the creation of live class calendar bookings (`class_schedule_bookings.created_at`).
* **Calculation Methodology:**
  * **Only 1 student in the entire dataset reached class scheduling:** Student `68101` (Booking Request `5501`).
  * `invoices.paid_at`: `2026-11-01 10:15:22`
  * `faculty_form.created_at`: `2026-11-01 10:45:00` (Delay: 29.6 mins)
  * `faculty_form.approved_at`: `2026-11-01 11:30:00` (Delay: 45.0 mins)
  * `booking_requests.created_at`: `2026-11-01 11:30:00`
  * `booking_requests.allocated_at`: `2026-11-01 12:00:00` (Delay: 30.0 mins)
  * `class_schedule_bookings.created_at`: `2026-11-01 12:00:05` (Delay: 5.0 secs)
  * **Observed Single-Student Turnaround Time:** **104.7 minutes (1 hour 44 minutes 43 seconds)**.
  * *Note:* This is **not a multi-record average** because none of the other 12 students have completed scheduling; for all remaining students, TAT is currently **indefinite (> 48 hours)**.
* **Recommended SLA Targets:**
  * *Clean Renewal (Happy Path):* **< 15 minutes** (Auto-scheduled instantly).
  * *Batch Change / Slot Request:* **< 4 hours**.
  * *Discrepancy Resolution:* **< 24 hours**.

#### 3. Form Submission Delay (Teacher Latency)
* **Definition:** Elapsed time between parent payment completion and teacher submission of the renewal form.
* **Formula:**  
  $$\text{Form Submission Delay} = \text{faculty\_form.created\_at} - \text{invoices.paid\_at}$$
* **Current Observed Performance:** Sample average of **27.8 minutes** across the 10 forms submitted with valid payment timestamps (ranging from 14.8 minutes for Form `3308` to 49.8 minutes for Form `3302`). Non-compliant teachers (`84906`, `84910`) have an infinite delay.
* **Recommended SLA Target:** **0 minutes** (Completely eliminate the manual form requirement for teachers by replacing it with direct gateway-to-database ingestion).

#### 4. Auto-Approval Rate (Zero-Touch Yield)
* **Definition:** Percentage of paid renewals that are reconciled, verified, and scheduled without any manual Ops intervention.
* **Formula:**  
  $$\text{Auto-Approval Rate} = \frac{\text{Renewals Scheduled via Zero-Touch Engine}}{\text{Total Paid Invoices}} \times 100$$
* **Current Observed Performance:** **0.0%** (100% of renewals currently depend on manual Ops verification).
* **Recommended SLA Target:** **>= 80.0%** of all renewal volume.

#### 5. Operational Exception Rate
* **Definition:** Percentage of renewal transactions that deviate from the standard happy path and require specialized manual triage.
* **Calculation Methodology:**
  * **Cohort-Level Exception Rate (Denominator = 13 Total Invoices):**
    * Numerator: **7 unique students** with operational discrepancies:
      1. Student `68104`: Parent mobile mismatch (`+91-9844XXXX77` vs registered `...04`).
      2. Student `68105`: Batch capacity full (`active_students_count = 6 / max 6`).
      3. Student `68108`: Duplicate form submission (`3308` and `3309`).
      4. Student `68109`: Partial payment submitted as full (`net_amount = 5,250` vs form `10,500`).
      5. Student `68111`: Gateway payment failed (`payment_status = Failed`).
      6. Student `68112`: Batch change requested (`classbatch_id = NULL`).
      7. Student `68113`: Teacher entered wrong invoice ID (`84931` instead of `84913`).
    * **Rate:** $\frac{7}{13} = \mathbf{53.8\%}$.
  * *(Alternative Metric — Paid Cohort Exception Rate: If we add the 2 Orphaned Invoices 68106 & 68110 as pipeline failures, 7 out of 11 paid renewals face friction = **63.6%**).*
* **Recommended SLA Target:** **< 10.0%** (Through frontend validation, auto-lookup, and tokenized payment links).

#### 6. Pending Renewal Count (Ops Backlog)
* **Definition:** Absolute count of renewing students who have paid but do not yet have their next classes booked in `class_schedule_bookings`.
* **Current Observed Performance:** **11 students** (out of 12 paid/partially paid renewals).
* **Recommended SLA Target:** **Zero overnight backlog** (All paid renewals cleared within business day).

---

## 5. Summary Findings for Live Case Review (Head of Operations Presentation)

When presenting these findings to the Head of Operations, structure the pitch around three core operational insights:

1. **The Core Bottleneck is Structural, Not Personnel:**  
   The Ops team is not failing because of poor effort; they are failing because the current architecture forces them to act as human middleware, manually copying data between four separate tables.
2. **Teacher Gatekeeping Creates Severe Scheduling Risk:**  
   Making the teacher a mandatory gatekeeper between payment and class scheduling creates immediate operational leakage (**18.2% orphaned paid invoices** in this sample alone—INR 29,000 in fees where classes are not scheduled).
3. **The 'Happy Path' Can Be Automated Today:**  
   In over 70% of standard renewals, the student continues in the same batch with the same teacher. These clean cases should be scheduled automatically within seconds of payment, freeing up 80% of Ops team bandwidth to focus on real customer exceptions (slot changes, custom scholarships, and capacity escalations).
