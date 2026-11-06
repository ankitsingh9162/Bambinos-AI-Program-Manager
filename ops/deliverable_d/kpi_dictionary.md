# Operations KPI Dictionary & Measurement Formulas

**Document Code:** DIC-OPS-MET-003  
**Role:** Senior AI Program Manager (Operations)  
**Organization:** Bambinos.live  
**Document Purpose:** Provide rigorous, standardized mathematical definitions, numerators, denominators, measurement frequencies, and operational caveats for all 15 key performance indicators governing the renewal pipeline.

---

## 1. Executive Master Metric Summary

```
+-------------------------------------------------------------------------------------------------------------------------------+
| KPI # | Metric Name                           | Formula Summary                                     | Proposed Target SLA     |
+-------------------------------------------------------------------------------------------------------------------------------+
| 1     | Auto-Approval Yield (Clean Renewals)  | (Auto-Approved Renewals / Total Paid Invoices) * 100| >= 80.0%                |
| 2     | Paid Invoice to Form Conversion       | (Submitted Forms / Total Paid Invoices) * 100       | 100.0% (Or Form Bypassed|
| 3     | Paid Students Awaiting Form (Orphaned)| Count of Paid Invoices with No Form after 2 Hours   | 0 Students              |
| 4     | Unresolved Exception Rate             | (Unresolved Exceptions / Total Renewals) * 100      | < 10.0%                 |
| 5     | Exception Resolution Time             | Timestamp Resolved - Timestamp Flagged              | P0: <1h | P1: <3h       |
| 6     | Payment-to-Approval Turnaround Time   | Timestamp Approved - Timestamp Paid                 | < 5 Minutes (Auto)      |
| 7     | Approval-to-Scheduling Time           | Timestamp Scheduled - Timestamp Approved            | < 10 Seconds (Auto)     |
| 8     | End-to-End Renewal Turnaround Time    | Timestamp Scheduled - Timestamp Paid                | < 15 Minutes (Clean)    |
| 9     | Batch Capacity Utilization            | (Active Enrolled Students / Max Batch Capacity) *100| 85.0% - 95.0%           |
| 10    | Batch Full Rate                       | (Batches at Max Capacity / Total Active Batches)*100| Monitor (< 15.0%)       |
| 11    | Duplicate Submission Rate             | (Duplicate Forms / Total Form Submissions) * 100    | < 2.0%                  |
| 12    | Notification Delivery Rate            | (Delivered WhatsApp Messages / Total Dispatched)*100| >= 98.0%                |
| 13    | Operational SLA Compliance Rate       | (Renewals Meeting SLA / Total Renewals) * 100       | >= 95.0%                |
| 14    | Overnight Pending Backlog             | Count of Paid Renewals Unscheduled at Day-End       | 0 Students              |
| 15    | Paid but Not Scheduled Students       | Rolling Count of Paid Students without Classes      | Zero > 24 Hours         |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

## 2. In-Depth Metric Definitions, Formulas & Caveats

### KPI 1: Auto-Approval Yield (Zero-Touch Ratio)
* **Business Meaning:** The proportion of paying renewal parents whose next term classes are completely scheduled without requiring manual Ops verification or data entry.
* **Mathematical Formula:**
  $$\text{Auto-Approval Yield} = \left( \frac{\text{Unique Renewals Auto-Approved by Zero-Touch Engine}}{\text{Total Successfully Paid Invoices}} \right) \times 100$$
* **Numerator:** Count of unique paid student renewals meeting all happy-path criteria (5 in prototype dataset).
* **Denominator:** Total invoices marked `Paid` at the payment gateway (11 in prototype dataset).
* **Current Prototype Baseline:** **45.5%** (5 / 11 Paid).
* **Proposed Operational Target:** **>= 80.0%** at full production rollout.
* **Important Caveat:** Denominator must use **Paid Invoices**, not total invoices (excluding failed or partial payments).

---

### KPI 2: Paid Invoice to Renewal Form Conversion
* **Business Meaning:** The percentage of paying parents whose teacher actually submits the required administrative renewal form.
* **Mathematical Formula:**
  $$\text{Invoice to Form Conversion} = \left( \frac{\text{Unique Paid Invoices with Submitted Faculty Form}}{\text{Total Successfully Paid Invoices}} \right) \times 100$$
* **Current Prototype Baseline:** $\frac{9}{11} = \mathbf{81.8\%}$.
* **Proposed Operational Target:** **100.0%** (or 0% teacher form requirement under the inverted webhook architecture).

---

### KPI 3: Paid Students Awaiting Form (Orphaned Invoice Count)
* **Business Meaning:** The absolute volume of paying students at high risk of class interruption because their teacher omitted the administrative renewal form.
* **Mathematical Formula:**
  $$\text{Orphaned Count} = \sum \text{Invoices} \text{ where } (\text{status} = \text{'Paid'} \land \text{age} > 2\text{h} \land \text{form\_id IS NULL})$$
* **Current Prototype Baseline:** **2 students** (`68106` - INR 18,000; `68110` - INR 11,000). Total fees at scheduling risk: INR 29,000.
* **Proposed Operational Target:** **0 students** (automated alerts trigger at 2h threshold).
* **Important Caveat:** Do not describe this as "confirmed lost revenue" since the fees were collected; it represents severe **scheduling risk, parent churn risk, and operational leakage**.

---

### KPI 4: Unresolved Exception Rate
* **Business Meaning:** The proportion of renewal transactions that hit blocking business or technical discrepancies and must be routed to human queues.
* **Mathematical Formula:**
  $$\text{Unresolved Exception Rate} = \left( \frac{\text{Unique Students with Unresolved Blocking Exceptions}}{\text{Total Unique Invoiced Students}} \right) \times 100$$
* **Current Prototype Baseline:** $\frac{8}{13} = \mathbf{61.5\%}$.
* **Proposed Operational Target:** **< 10.0%** across scaled steady-state operations.
* **Important Caveat:** Non-blocking resolved warnings (such as identical duplicate forms or unambiguous single typos) must **not** be included in the unresolved numerator.

---

### KPI 5: Exception Resolution Time
* **Business Meaning:** The elapsed duration from the timestamp an exception is flagged on the dashboard to the timestamp an Ops agent marks it resolved.
* **Mathematical Formula:**
  $$\text{Resolution Time} = \text{Timestamp}_{\text{Exception Closed}} - \text{Timestamp}_{\text{Exception Flagged}}$$
* **Proposed Operational Targets:**
  * P0 (Payment Failed): **< 1 Hour**
  * P1 (Batch Full, Missing Form, Partial Payment): **< 3 Hours**
  * P2 (Phone Mismatch, Scholarship Sign-off): **< 4 Hours**

---

### KPI 6: Payment-to-Approval Turnaround Time
* **Business Meaning:** Time elapsed from payment settlement at gateway to formal renewal approval.
* **Mathematical Formula:**
  $$\text{TAT}_{\text{Approval}} = \text{Timestamp}_{\text{Approval}} - \text{Timestamp}_{\text{Invoice Paid}}$$
* **Current Prototype Baseline:** For Student `68101`, legacy manual approval took **74.6 minutes** (10:15:22 to 11:30:00).
* **Proposed Operational Target:** **< 5 minutes** via automated zero-touch engine.

---

### KPI 7: Approval-to-Scheduling Time
* **Business Meaning:** Time elapsed from renewal approval to calendar class booking creation.
* **Mathematical Formula:**
  $$\text{TAT}_{\text{Scheduling}} = \text{Timestamp}_{\text{Schedule Created}} - \text{Timestamp}_{\text{Approval}}$$
* **Current Prototype Baseline:** For Student `68101`, legacy Ops batch allocation and scheduling took **30.1 minutes** (11:30:00 to 12:00:05).
* **Proposed Operational Target:** **< 10 seconds** via programmatic database insert.

---

### KPI 8: End-to-End Renewal Turnaround Time (TAT)
* **Business Meaning:** Total elapsed customer time from the moment the parent pays to the moment active classes are confirmed in their calendar.
* **Mathematical Formula:**
  $$\text{TAT}_{\text{End-to-End}} = \text{Timestamp}_{\text{Class Schedule Created}} - \text{Timestamp}_{\text{Invoice Paid}}$$
* **Current Prototype Baseline:** **104.7 minutes** (observed strictly on the single completed student `68101`).
* **Proposed Operational Targets:**
  * Clean Renewals (Happy Path): **< 15 minutes**
  * Exception Renewals (Batch Change / Discounts): **< 4 hours**
* **Important Caveat:** **Never present 104.7 minutes as a multi-record average**. It is the single-case empirical measurement of student `68101`. For all other 12 students in the historical cohort, TAT is currently indefinite (> 48h).

---

### KPI 9: Batch Capacity Utilization
* **Business Meaning:** The density and efficiency of active live student batches.
* **Mathematical Formula:**
  $$\text{Capacity Utilization} = \left( \frac{\text{Total Active Enrolled Students}}{\text{Total Batch Capacity Slots}} \right) \times 100$$
* **Current Reference Baseline:** In `reference_active_batches_and_students.csv`, average utilization across active batches is **76.9%** (most batches have 4 or 5 students out of 6).
* **Proposed Operational Target:** **85.0% – 95.0%** to maximize educator teaching efficiency.

---

### KPI 10: Batch Full Rate
* **Business Meaning:** Percentage of active student batches that have reached maximum capacity (6/6), requiring sister batch routing.
* **Mathematical Formula:**
  $$\text{Batch Full Rate} = \left( \frac{\text{Batches with Active Students} == \text{Max Capacity}}{\text{Total Active Class Batches}} \right) \times 100$$
* **Current Reference Baseline:** Batch `9205` is full (6/6), representing **7.7%** of batches in reference data.
* **Proposed Operational Target:** Monitor continuously (< 15.0% to prevent widespread parent displacement).

---

### KPI 11: Duplicate Submission Rate
* **Business Meaning:** Percentage of faculty renewal submissions that represent duplicate attempts.
* **Mathematical Formula:**
  $$\text{Duplicate Rate} = \left( \frac{\text{Duplicate Form Submissions}}{\text{Total Faculty Form Submissions}} \right) \times 100$$
* **Current Prototype Baseline:** $\frac{1}{12} = \mathbf{8.3\%}$ (Form `3309` submitted after browser freeze).
* **Proposed Operational Target:** **< 2.0%** via frontend debouncing and submission lockouts.

---

### KPI 12: Notification Delivery Rate
* **Business Meaning:** Percentage of auto-generated message drafts successfully transmitted and delivered to recipients.
* **Mathematical Formula:**
  $$\text{Delivery Rate} = \left( \frac{\text{Delivered WhatsApp / Slack Messages}}{\text{Total Outbound Messages Attempted}} \right) \times 100$$
* **Current Prototype Baseline:** **N/A (Drafts Only)**. Exactly **27 notification drafts** were generated by the prototype; zero messages were sent in simulation mode.
* **Proposed Operational Target:** **>= 98.0%** upon WhatsApp Business Cloud API activation.

---

### KPI 13: Operational SLA Compliance Rate
* **Business Meaning:** Overall proportion of renewal cases resolved and scheduled within their assigned priority SLA window.
* **Mathematical Formula:**
  $$\text{SLA Compliance Rate} = \left( \frac{\text{Renewals Fully Scheduled Within Target SLA}}{\text{Total Paid Renewal Transactions}} \right) \times 100$$
* **Proposed Operational Target:** **>= 95.0%** across weekly operations.

---

### KPI 14: Overnight Pending Backlog
* **Business Meaning:** The absolute count of paying students whose renewal classes remain unscheduled at end-of-day (07:00 PM).
* **Current Prototype Baseline:** **11 students** awaiting class scheduling in sample cohort.
* **Proposed Operational Target:** **0 students** overnight backlog.

---

### KPI 15: Paid but Not Scheduled Students
* **Business Meaning:** Active rolling headcount of paying parents waiting for class confirmation.
* **Mathematical Formula:**
  $$\text{Unscheduled Headcount} = \text{Count of Students with Paid Invoices} - \text{Count of Students with Active Scheduled Bookings}$$
* **Current Prototype Baseline:** **10 students** (11 Paid - 1 Scheduled Student `68101`).
* **Proposed Operational Target:** Zero students older than 24 hours.
