# Operations Risk Register, Dependencies & Leadership Decisions

**Document Code:** RSK-OPS-REN-004  
**Role:** Senior AI Program Manager (Operations)  
**Organization:** Bambinos.live  
**Scope:** Re-Engineering & Automating the Student Renewal -> Class Scheduling Pipeline  
**Document Purpose:** Detail technical and operational vulnerabilities, failure modes, mitigation protocols, implementation dependencies, and the formal policy decisions required from Operations Leadership prior to production rollout.

---

## 1. Operations Risk Register & Mitigation Matrix

```
+---------------------------------------------------------------------------------------------------------------------------------------+
| Risk & Failure Mode            | Prob.  | Impact | Root Cause & Operational Impact            | Mitigation & Control Protocol | Owner |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 1. Payment Webhook Latency /   | Medium | High   | Webhook drops or network timeouts delay    | Implement idempotent polling  | Sys.  |
|    Drop                        |        |        | payment confirmation, stalling pipeline.   | worker running every 15 mins. | Spec. |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 2. Payer Phone Number Mismatch | High   | Medium | Parent pays using secondary mobile/spouse  | Tokenize payment links with   | Prod. |
|                                |        |        | phone, causing automated lookup failure.   | student_id; family profile DB.| Lead  |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 3. Concurrent Over-Booking /   | Medium | High   | Two students allocated to last open seat   | Enforce atomic database locks | Data  |
|    Race Condition              |        |        | simultaneously during peak hours.          | (UPDATE ... WHERE count < max)| Ops   |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 4. Batch Overcapacity          | High   | High   | Student pitched into batch already 6/6;   | Reserve student seat 7 days   | Acad. |
|    Displacement                |        |        | abrupt scheduling failure and friction.    | before term end; sister batch.| Ops   |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 5. Teacher Omission of Renewal | High   | High   | Teachers forget manual Google Form, leaving| Invert pipeline: Webhook is   | Ops   |
|    Form (Orphaned Invoices)    |        |        | paid renewals in silent limbo (18.2% rate).| primary trigger; 1-tap nudge. | Head  |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 6. Unverified UPI Screenshots  | Medium | High   | Teachers submit renewal form based on fake | Enforce strict rule: Gateway  | Fin.  |
|    Accepted by Educators       |        |        | or pending UPI payment proof (Form 3311).  | settlement ID is mandatory.   | Lead  |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 7. WhatsApp Template Block /   | Low    | High   | Meta rejects template or parent opts out of| Multi-channel fallback: Auto- | Prod. |
|    Opt-Out                     |        |        | WhatsApp, blocking self-service picker.    | send SMS link / Ops outbound. | Lead  |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 8. Ambiguous Invoice Typo      | Low    | Medium | Educator enters invoice ID belonging to a  | Dropdown-only entry in teacher| Prod. |
|                                |        |        | different student, causing false match.    | portal; single-match rule.    | Lead  |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 9. LLM Hallucination / Scope   | Low    | High   | Generative AI model makes unauthorized     | Strict boundary: Zero LLM     | AI    |
|    Creep                       |        |        | financial approval or price waiver.        | financial authority; code only| Lead  |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 10. Mass System Outage / Crash | Low    | High   | n8n server or database downtime during peak| 1-click Ops manual override;  | Sys.  |
|                                |        |        | weekend renewal cycle.                     | fallback to manual spreadsheets| Spec. |
+---------------------------------------------------------------------------------------------------------------------------------------+
```

---

## 2. Core Technical & Operational Implementation Dependencies

The re-engineered zero-touch workflow relies on the following core dependencies:

1. **Payment Gateway Webhook Configuration:**
   * *Dependency:* Payment gateways (Razorpay / Stripe) must emit real-time webhook payloads containing transaction IDs and custom metadata tags (`student_id`, `user_id`, `course_id`).
   * *Status:* Confirmed industry capability; requires engineering webhook endpoint setup in Phase 1.
2. **ACID-Compliant Relational Database Migration:**
   * *Dependency:* Migration from standalone CSVs/Google Sheets to PostgreSQL / Supabase to enable row-level concurrency locking (`UPDATE classbatches ... WHERE active_students_count < max_batch_size`).
   * *Status:* Architectural recommendation; essential to prevent race conditions during peak renewal windows.
3. **Meta WhatsApp Business Cloud API Access:**
   * *Dependency:* Approved Meta WhatsApp Business Account via Business Solution Providers (e.g., WATI, Gupshup, or Twilio) with pre-approved message templates for slot selection, schedule confirmation, and balance reminders.
   * *Status:* Operational dependency; templates must be submitted for Meta approval during Days 0–30.
4. **Internal Ops Escalation Channels:**
   * *Dependency:* Slack API integration with webhook endpoints connecting n8n to internal operations channels (`#ops-approvals`, `#ops-triage`).
   * *Status:* Readily available; configured in Phase 2.

---

## 3. Decisions Required from Operations Leadership

Prior to launching Phase 2 live pilot execution, the following formal operational decisions must be approved by the **Head of Operations** and **Executive Leadership**:

```
+-------------------------------------------------------------------------------------------------------------------------------+
| Decision Area                  | Options & Trade-Offs Considered                         | Proposed Recommendation     |
+-------------------------------------------------------------------------------------------------------------------------------+
| 1. Batch Capacity Policy       | Option A: Strict, immutable 6-student ceiling.           | **Option A (Strict Cap)**:  |
|                                | Option B: Allow temporary +1 expansion (max 7) for      | Preserves educational       |
|                                | renewing students with manager sign-off.                 | quality; prevents overload. |
+-------------------------------------------------------------------------------------------------------------------------------+
| 2. Scholarship Approval        | Option A: All discounts (>0%) require Ops Head approval. | **Option B (Tiered Matrix)**|
|    Thresholds                  | Option B: Tiered policy (<= 10% auto-allowed for tenure  | Prevents executive bottle-  |
|                                | > 6 months; 11-20% Ops Lead; > 20% Ops Head).           | necks on routine renewals.  |
+-------------------------------------------------------------------------------------------------------------------------------+
| 3. Teacher Attribution When    | Option A: Retain simplified teacher Google Form.         | **Option B (Roster Link)**: |
|    Form is Bypassed            | Option B: Attribute renewal commission directly to the   | Eliminates teacher form     |
|                                | student's current active teacher in reference roster.    | delay; protects incentives. |
+-------------------------------------------------------------------------------------------------------------------------------+
| 4. Safe Invoice Typo Auto-     | Option A: Always escalate any invoice typo to Ops Tier 1.| **Option B (Single Match)**:|
|    Correction Policy           | Option B: Auto-reconcile ONLY IF the student has exactly| Balances automation velocity|
|                                | 1 paid invoice and matching amount (as in Form 3313).    | with financial safety.      |
+-------------------------------------------------------------------------------------------------------------------------------+
| 5. Booking Idempotency & Retry | Option A: Hard database block on duplicate submissions.  | **Option B (Idempotent)**:  |
|    Policy                      | Option B: Merge identical duplicates as resolved warnings| Eliminates duplicate seats  |
|                                | while escalating conflicting submissions to Ops.         | without halting workflow.   |
+-------------------------------------------------------------------------------------------------------------------------------+
| 6. Definition of Scheduling    | Option A: Student schedule confirmed when booking created| **Option B (Calendar Booked)|
|    Confirmation                | in Table 3.                                              | Prevents false reporting;   |
|                                | Option B: Student schedule confirmed ONLY when live      | guarantees teacher and room |
|                                | session rows are inserted in Table 4.                    | allocation are finalized.   |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Emergency Fallback & Manual Override Protocol

In the event of a system disruption, gateway outage, or database lock, Operations enforces the following **Emergency Fallback Protocol**:

1. **Dashboard 1-Click Kill Switch:**
   * The Operations Head retains a global `AUTOMATION_HALT` toggle on the daily dashboard.
   * Activating this toggle immediately freezes automated scheduling and messaging pipelines.
2. **Graceful Fallback to Staged Queues:**
   * All incoming payments continue to be ingested into `1_invoices` without loss.
   * Auto-approval transactions are held in a staged `QUEUED_FOR_BATCH_APPROVAL` queue.
3. **Manual Override Console:**
   * Ops executives use the Retool / Streamlit Action Table to manually allocate batches and verify schedules in 1-click while audit logs record the manual actor.
4. **Resumption & Idempotent Catch-Up:**
   * When systems are restored, the engine processes queued records chronologically using composite idempotency keys (`student_id + invoice_id`), ensuring zero duplicate entries.
