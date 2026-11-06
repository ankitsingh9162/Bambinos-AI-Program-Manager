# Operational KPIs & Recommended SLA Targets (Validated)

**Document Purpose:** Define measurable operational performance indicators, formulas, current empirical baselines, and recommended SLA targets for the Bambinos.live Student Renewal -> Class Scheduling pipeline.  
**Audience:** Head of Operations, Program Managers, Operations Team Leads.  
**Disclaimer:** All proposed SLA targets represent operational design recommendations and industry benchmarks, not pre-existing company policies.

---

## 1. Executive Metric Scorecard

| KPI Name | Current Baseline (Empirical) | Recommended SLA Target | Measurement Frequency | Business Impact |
| :--- | :---: | :---: | :---: | :--- |
| **Orphaned Invoice Rate (Paid)** | **18.2%** (2 / 11 Paid) | **0.0%** (< 2h alert) | Real-time / Hourly | Prevents paid parents from falling into scheduling limbo |
| **Payment-to-Schedule TAT** | **104.7 mins** (Single student) | **< 15 mins** (Happy Path) | Per Transaction | Eliminates class continuity interruptions |
| **Form Submission Delay** | **27.8 mins avg** | **0 mins** (Bypassed) | Per Transaction | Removes teacher administrative dependency |
| **Auto-Approval Rate** | **0.0%** (0 / 11 Paid) | **>= 80.0%** | Daily / Weekly | Scales renewal operations without adding headcount |
| **Operational Exception Rate** | **53.8%** (7 / 13 Cohort) | **< 10.0%** | Daily / Weekly | Drastically cuts Ops manual investigation time |
| **Pending Renewal Backlog** | **11 students** | **0 overnight backlog** | End of Day (EOD) | Eliminates parent follow-ups and escalation tickets |

---

## 2. In-Depth Operational KPI Breakdown

### 2.1 Orphaned Invoice Rate
* **Definition:** The proportion of successfully completed renewal payments (`payment_status = Paid` in `1_invoices.csv`) that have no matching faculty submission or booking record within a designated grace window.
* **Calculation Formula:**
  $$\text{Orphaned Invoice Rate (Paid)} = \frac{\text{Count of Invoices with Status 'Paid' and No Downstream Record}}{\text{Total Invoices with Status 'Paid'}} \times 100$$
* **Empirical Analysis in Dataset:**
  * Total Invoices in Cohort: **13**
    * `Paid`: **11** (`84901`, `84902`, `84903`, `84904`, `84905`, `84906`, `84907`, `84908`, `84910`, `84912`, `84913`)
    * `Partially_Paid`: **1** (`84909` - INR 5,250 received of INR 10,500)
    * `Failed`: **1** (`84911` - INR 12,000 transaction failed at gateway)
  * Paid Invoices with no faculty submission: **2** (`84906` - Student `68106` / INR 18,000; `84910` - Student `68110` / INR 11,000). Total renewal fees at scheduling risk: **INR 29,000**.
  * **Paid Invoices Orphaned Rate:** $\frac{2}{11} = \mathbf{18.2\%}$.
  * *(Cohort-Wide Orphaned Rate across all 13 invoices: $\frac{2}{13} = 15.4\%$)*.
* **Recommended Operational SLA:** **0.0%**. In the re-engineered architecture, payment gateway webhooks trigger automatic renewal workflows immediately upon payment completion, rendering orphaned invoices structurally impossible.

---

### 2.2 Payment-to-Schedule Turnaround Time (TAT)
* **Definition:** The total elapsed duration from the exact timestamp a payment gateway marks a payment as `Paid` (`1_invoices.paid_at`) to the creation of active calendar sessions in `4_class_schedule_bookings.created_at`.
* **Calculation Formula:**
  $$\text{Turnaround Time (minutes)} = \frac{\text{Timestamp}_{\text{class\_schedule\_bookings.created\_at}} - \text{Timestamp}_{\text{invoices.paid\_at}}}{60}$$
* **Empirical Verification in Dataset:**
  * **Critical Note:** This metric represents **one single completed student** (`68101`), **not an average across multiple records**, because none of the other 12 students in the dataset have reached class scheduling.
  * Complete Event Timeline for Student `68101` (Booking Request `5501`):
    * `invoices.paid_at`: `2026-11-01 10:15:22`
    * `faculty_form.created_at`: `2026-11-01 10:45:00` (Teacher submission lag: **29.6 minutes**)
    * `faculty_form.approved_at`: `2026-11-01 11:30:00` (Ops review latency: **45.0 minutes**)
    * `booking_requests.created_at`: `2026-11-01 11:30:00`
    * `booking_requests.allocated_at`: `2026-11-01 12:00:00` (Ops batch allocation latency: **30.0 minutes**)
    * `class_schedule_bookings.created_at`: `2026-11-01 12:00:05` (Calendar booking: **5.0 seconds**)
  * **Total Elapsed TAT:** **104.7 minutes (1 hour 44 minutes 43 seconds)**.
  * For all remaining 12 students in the dataset, TAT is currently **indefinite (> 48 hours)**.
* **Recommended Operational SLA Targets:**
  * **Tier 1 (Happy-Path Clean Renewals): < 15 minutes** (Target: Instantaneous < 1 minute via zero-touch automation).
  * **Tier 2 (Batch Change / Slot Request): < 4 hours**.
  * **Tier 3 (Payment Discrepancies / Escalations): < 24 hours**.

---

### 2.3 Form Submission Delay (Teacher Hand-off Latency)
* **Definition:** The time lag between the parent's payment completion and the faculty member submitting the manual renewal form.
* **Calculation Formula:**
  $$\text{Teacher Latency (minutes)} = \frac{\text{Timestamp}_{\text{faculty\_form.created\_at}} - \text{Timestamp}_{\text{invoices.paid\_at}}}{60}$$
* **Empirical Analysis in Dataset:**
  * Sample size: 10 records with valid timestamps.
  * Average: **27.8 minutes**.
  * Minimum: **14.8 minutes** (Form `3308`).
  * Maximum: **49.8 minutes** (Form `3302`).
  * Note: This measures only compliant teachers. For non-compliant teachers (`84906`, `84910`), the delay is indefinite.
* **Recommended Operational SLA Target:** **0 minutes**. Eliminate the teacher form submission requirement entirely for standard renewals.

---

### 2.4 Auto-Approval Rate (Zero-Touch Ratio)
* **Definition:** The percentage of paid renewal requests processed from payment to final class scheduling without human Ops touchpoints.
* **Calculation Formula:**
  $$\text{Auto-Approval Rate} = \frac{\text{Total Renewals Scheduled Without Human Ops Intervention}}{\text{Total Completed Paid Renewals}} \times 100$$
* **Empirical Analysis in Dataset:**
  * Current: **0.0%** (100% of rows in `2_faculty_form_unapproved.csv` require manual review by an Ops agent, e.g., `ops_exec_01`, `ops_exec_02`, `ops_exec_03`).
* **Recommended Operational SLA Target:** **>= 80.0%**. The vast majority of renewals are same-batch, same-teacher, and full-fee, making them prime candidates for end-to-end automation.

---

### 2.5 Operational Exception Rate
* **Definition:** The fraction of renewal transactions that deviate from the standard happy path and require specialized manual triage.
* **Calculation Methodology:**
  * **Cohort-Wide Exception Rate (Denominator = 13 Total Invoices):**
    * Numerator: **7 unique students** with operational discrepancies:
      1. Student `68104`: Parent mobile mismatch (`+91-9844XXXX77` vs registered `...04`).
      2. Student `68105`: Batch capacity full (`active_students_count = 6 / max 6`).
      3. Student `68108`: Duplicate form submission (`3308` and `3309`).
      4. Student `68109`: Partial payment submitted as full (`net_amount = 5,250` vs form `10,500`).
      5. Student `68111`: Gateway payment failed (`payment_status = Failed`).
      6. Student `68112`: Batch change requested (`classbatch_id = NULL`).
      7. Student `68113`: Teacher entered wrong invoice ID (`84931` instead of `84913`).
    * **Cohort Rate:** $\frac{7}{13} = \mathbf{53.8\%}$.
  * **Paid-Cohort Exception Rate (Denominator = 11 Paid Invoices):**
    * If evaluating purely against parents who successfully paid in full, adding the 2 Orphaned Invoices (`68106`, `68110`) as operational failures results in 7 out of 11 paid renewals hitting friction = **63.6%**.
* **Recommended Operational SLA Target:** **< 10.0%**. Implemented via strict frontend input constraints, real-time gateway checks, and automated student lookup.

---

### 2.6 Pending Renewal Backlog (Queue Health)
* **Definition:** The net volume of paying students waiting in operational limbo between payment and class scheduling at any given point in time.
* **Empirical Analysis in Dataset:**
  * Current Backlog: **11 students** awaiting class schedule creation.
* **Recommended Operational SLA Target:**
  * Real-time Queue Depth: **< 5 pending items**.
  * Aging SLA: **0 items older than 24 hours at EOD**.

---

## 3. SLA Escalation Matrix

When an exception occurs or an SLA threshold is breached, the following tiered escalation matrix activates automatically:

```
+---------------------------------------------------------------------------------------------------------+
|                                    OPERATIONAL ESCALATION MATRIX                                        |
+---------------------------------------------------------------------------------------------------------+
| Severity Level  | Trigger Condition                  | Resolution Owner       | Max Resolution SLA      |
+---------------------------------------------------------------------------------------------------------+
| Level 1 (Low)   | Contact Mismatch / Browser Dup     | Ops Executive (Tier 1) | 2 Hours                 |
| Level 2 (Med)   | Batch Full / Slot Change Request   | Academic Counselor     | 4 Hours                 |
| Level 3 (High)  | Partial Payment / Payment Failed   | Finance / Retention Lead| 6 Hours                |
| Level 4 (Crit)  | Orphaned Paid Invoice > 2 Hours    | Head of Operations     | 1 Hour                  |
+---------------------------------------------------------------------------------------------------------+
```
