# Automation Safeguards & Governance Architecture (Validated)

**Role:** AI Program Manager (Operations)  
**Organization:** Bambinos.live  
**Document Purpose:** Define operational guardrails, boundary constraints, anti-hallucination policies, and audit logging to ensure automated operations remain fail-safe, fraud-resistant, and auditable at scale.  
**Companion Documents:**
- [`workflow_architecture.md`](file:///c:/Users/hp/Downloads/mongodb%20project/AI-PM-hiring-take-home-assignments/ops/audit/workflow_architecture.md)
- [`exception_handling_matrix.csv`](file:///c:/Users/hp/Downloads/mongodb%20project/AI-PM-hiring-take-home-assignments/ops/audit/exception_handling_matrix.csv)
- [`workflow_diagram.mmd`](file:///c:/Users/hp/Downloads/mongodb%20project/AI-PM-hiring-take-home-assignments/ops/audit/workflow_diagram.mmd)

---

## 1. Five Core Non-Negotiable Safeguards

```
+---------------------------------------------------------------------------------------------------------+
|                                    FIVE CORE AUTOMATION SAFEGUARDS                                      |
+---------------------------------------------------------------------------------------------------------+
|  1. FINANCIAL GROUND TRUTH        | Under no circumstances are classes scheduled based solely on a      |
|                                   | teacher's claim of payment or a parent chat screenshot. A verified, |
|                                   | settled payment gateway record is strictly mandatory.               |
|  2. LLM ROLE RESTRICTION          | LLMs are strictly restricted to unstructured language parsing and  |
|                                   | message drafting. ZERO decision-making authority over financial,   |
|                                   | pricing, discounting, or batch allocation rules.                   |
|  3. IDEMPOTENCY & DEDUPLICATION   | Every webhook, event, and database transaction generates a          |
|                                   | deterministic idempotency key to prevent duplicate class bookings.  |
|  4. HARD CAPACITY CEILINGS        | Atomic check-and-lock database operations prevent exceeding batch   |
|                                   | capacity limits (observed as max_batch_size = 6 in reference data). |
|  5. AUDIT LOGGING & OVERRIDE      | Every automated state transition writes an immutable audit record.  |
|                                   | Ops agents retain a 1-click manual override to halt automation.     |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. In-Depth Technical Implementation of Safeguards

### Safeguard 1: Mandatory Financial Ground Truth Verification
* **Vulnerability Identified in Production Dataset:**
  * Form `3311` (Student `68111`): Teacher submitted a renewal form with remark *"Parent shared UPI processing screenshot"*, but Invoice `84911` failed at the gateway (`payment_status = Failed`).
  * Form `3310` (Student `68109`): Teacher reported `amount_paid = 10,500`, but Invoice `84909` only had `net_amount = 5,250` (`payment_status = Partially_Paid`).
* **Implementation Rule:**
  * No class schedule record (`class_schedule_bookings`) may ever be created unless the referenced invoice has an explicit `payment_status == 'Paid'` settled at the gateway API with a valid `gateway_payment_id`.
  * Teacher form submissions and chat screenshots are treated purely as **contextual signals**, not financial ground truth.

---

### Safeguard 2: LLM Boundary Restrictions (Zero Financial / Approval Authority)
* **Design Boundary:** LLMs provide natural language understanding (e.g., interpreting unstructured teacher remarks or parsing parent WhatsApp replies), but must never be allowed to execute deterministic business or financial logic.
* **Prohibited LLM Actions:**
  1. The LLM **cannot** mark an invoice as paid or authorize payment status transitions.
  2. The LLM **cannot** grant, calculate, or approve discount percentages or scholarships.
  3. The LLM **cannot** directly write or mutate rows in `invoices`, `booking_requests`, or `class_schedule_bookings`.
* **Sanctioned LLM Tasks:**
  1. *Entity & Intent Extraction:* Extracting unstructured notes from teacher remarks (e.g., *"Mother paid from her number"* -> extract phone `+91-9844XXXX77`).
  2. *Empathetic Draft Generation:* Drafting friendly WhatsApp messages for parent slot selection or payment retry requests.
  3. *Schema Validation:* All LLM outputs must be constrained to a strict JSON schema before ingestion by the workflow engine (`n8n` / `Make`).

---

### Safeguard 3: Database Idempotency & Deduplication
* **Vulnerability Identified in Production Dataset:**
  * Forms `3308` and `3309` (Student `68108`, Invoice `84908`): Submitted 5 minutes apart by the same teacher due to a browser freeze, risking duplicate booking records and Ops confusion.
* **Implementation Rule:**
  * **Composite Idempotency Key:** Every automated transaction generates a deterministic hash:
    $$\text{Key} = \text{SHA256}(\text{student\_id} + \text{"\_"} + \text{invoice\_id} + \text{"\_"} + \text{session\_cycle})$$
  * **Unique Constraints:** The database enforces:
    * `UNIQUE (student_id, invoice_id)` on `booking_requests`
    * `UNIQUE (bookingrequest_id, class_date, start_time)` on `class_schedule_bookings`
  * **Deduplication Logic:** If a duplicate form submission arrives, the engine marks it `DUPLICATE_SUPPRESSED` and links it to the original form without re-triggering scheduling.

---

### Safeguard 4: Hard Batch Capacity Locking
* **Vulnerability Identified in Production Dataset:**
  * Booking Request `5505` / Form `3305` (Student `68105`): Teacher pitched renewal into Batch `9205`, but `reference_active_batches_and_students` shows `active_students_count = 6` and `max_batch_size = 6`, causing an abrupt `Failed_Batch_Full` error.
* **Implementation Rule:**
  * Capacity checks must be **atomic database transactions**, not in-memory checks:
    ```sql
    UPDATE classbatches 
    SET active_students_count = active_students_count + 1 
    WHERE id = :target_batch_id AND active_students_count < max_batch_size;
    ```
  * If zero rows are updated, the batch is full. The engine immediately routes the renewal to the `BATCH_FULL` exception queue and drafts alternative sister batch options, preventing over-enrollment beyond the verified capacity ceiling.

---

### Safeguard 5: Immutable Audit Logging & Manual Override Protocol
* **Immutable Audit Log Table (`audit_event_log`):**
  Every automated transition records:
  * `event_id` (UUID)
  * `timestamp` (UTC ISO-8601)
  * `entity_type` (`invoice`, `faculty_form`, `booking_request`, `class_schedule`)
  * `entity_id`
  * `actor` (`SYSTEM_ZERO_TOUCH_ENGINE`, `n8n_worker_01`, `ops_exec_02`)
  * `action` (`AUTO_APPROVED`, `EXCEPTION_FLAGGED`, `MANUAL_OVERRIDE`)
  * `reason_code` (`HAPPY_PATH_AUTO_APPROVED`, `PHONE_MISMATCH`, etc.)
  * `previous_state` vs `new_state` (JSON diff)
* **Manual Override Protocol:**
  * Ops leads have a 1-click `automation_halt` toggle on the dashboard to pause automation for any student, batch, or system-wide.
  * When paused, all automated messaging and calendar booking halts, returning control to manual Ops execution while preserving full audit logs.
