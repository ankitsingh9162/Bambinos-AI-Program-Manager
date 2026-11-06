# Standard Operating Procedure (SOP): Student Renewal -> Class Scheduling Pipeline

**Document Code:** SOP-OPS-REN-001  
**Version:** 1.0 (Operational Prototype Baseline)  
**Effective Date:** 2026-11-05  
**Audience:** 10-Person Operations Team, Academic Coordinators, Faculty Leadership (200+ Teachers)  
**Process Owner:** Head of Operations  

---

## 1. Purpose & Scope

This Standard Operating Procedure (SOP) governs the end-to-end operational execution of the **Student Renewal to Class Scheduling Pipeline** at Bambinos.live. It transitions the organization from a high-friction, error-prone manual handoff process across spreadsheets to an automated, exception-governed pipeline.

**Core Operational Directives:**
1. **Zero-Touch for Clean Renewals:** All recurring renewals meeting standard happy-path criteria (settled full payment, matching parent contact, same batch, and verified capacity) must be auto-approved and scheduled without manual Ops data entry.
2. **Financial Ground Truth:** No student may ever be booked into a class schedule based solely on an educator's verbal claim, text note, or payment screenshot. Direct payment gateway API confirmation (`payment_status == 'Paid'`) is non-negotiable.
3. **Capacity Integrity:** No student may be booked into a batch that exceeds maximum capacity (`max_batch_size = 6` in current reference standards).
4. **Target Operating Capacity:** Designed to enable a **10-person Operations team** to manage renewals for **200+ teachers** and thousands of students weekly by processing only exceptions.

---

## 2. End-to-End Workflow Stages (10-Stage SOP)

The table below defines all 10 stages of the pipeline:

```
+---------------------------------------------------------------------------------------------------------------------------------------+
| Stage & Name        | Trigger & Input               | Automated Engine Action        | Human Ops Action            | Target SLA & Owner |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 1. Payment Received | Parent completes payment via  | Ingest gateway transaction;   | None. System logs payment   | < 1 minute         |
|                     | link or portal.               | create row in `1_invoices`.    | event in audit trail.       | Payment Gateway API|
+---------------------------------------------------------------------------------------------------------------------------------------+
| 2. Webhook & Invoice| Gateway emits settlement      | Verify transaction status,     | None for 'Paid'. Review     | < 5 minutes        |
|    Verification     | payload (e.g. `payment.paid`).| net amount, currency, and fee. | Failed / Partial payments.  | Automated Engine   |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 3. Entity & Identity| Invoice recorded with         | Query `reference_data` by      | If phone differs, verify in | < 15 minutes       |
|    Matching         | `student_id` and payer phone. | `student_id`; verify mobile.   | family user profile.        | Automated / Ops T1 |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 4. Renewal Form     | Teacher submits renewal form  | Cross-match invoice ID and fee | None for clean matches.     | < 30 minutes       |
|    Validation       | in `faculty_form_unapproved`. | against gateway record.        | Flag discrepancies.         | Automated / Ops T1 |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 5. Duplicate Form   | Incoming form matches an      | Check field equality. If same, | If conflicting fields, Ops  | < 5 minutes        |
|    Deduplication    | existing `(student, invoice)`.| auto-merge as resolved warning.| reviews both forms.         | Automated / Ops T1 |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 6. Batch Capacity   | Renewal indicates batch ID    | Atomic check on active count;  | If full, offer 2 sister     | < 1 hour           |
|    Validation       | and `continue_same_batch`.    | lock seat if `count < max`.    | batches to parent.          | Automated / Ops T2 |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 7. Booking Request  | Auto-approval qualified or    | Re-link existing booking or    | Review pending allocations  | < 15 minutes       |
|    Generation/Reuse | exception resolved.           | create simulated booking ID.   | if manual batch needed.     | Automated / Ops T1 |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 8. Class Calendar   | Booking request marked        | Generate 24 session rows in    | Confirm first class date    | < 5 minutes        |
|    Scheduling       | ready for class booking.      | `class_schedule_bookings`.     | in batch calendar.          | Automated / Ops T1 |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 9. Parent & Teacher | Schedule generated in         | Dispatch WhatsApp template W1  | Handle parent replies if    | < 5 minutes        |
|    Notification     | calendar table.               | to parent and alert to teacher.| slot adjustments requested. | WhatsApp Cloud API |
+---------------------------------------------------------------------------------------------------------------------------------------+
| 10. Exception Triage| Transaction deviates from     | Log exact Reason Code; dispatch| Execute resolution protocol | P0: < 15m; P1: <2h |
|     & Closure       | standard happy path.          | targeted drafts to owner.      | and mark exception closed.  | Ops Tier 1/2 / Lead|
+---------------------------------------------------------------------------------------------------------------------------------------+
```

---

## 3. Exception Handling Action Guide (By Reason Code)

Every exception flagged by the reconciliation engine is governed by a strict handling protocol:

```
+----------------------------------------------------------------------------------------------------------------------------------+
| Reason Code                    | Class & Severity | Required Operational Handling                               | Escalation SLA & Owner |
+----------------------------------------------------------------------------------------------------------------------------------+
| 1. PHONE_MISMATCH              | Unresolved (P2)  | Payer phone differs from registered profile (e.g. mother    | 2 Hours                |
|                                |                  | paid from unlinked number). Cross-reference user ID in      | Ops Tier 1             |
|                                |                  | master user table. Confirm family link in 1-click.          |                        |
+----------------------------------------------------------------------------------------------------------------------------------+
| 2. BATCH_FULL                  | Unresolved (P1)  | Target batch is at max capacity (6/6). Check sister batches | 3 Hours                |
|                                |                  | with identical grade/subject. Offer 2 options to parent via | Academic Ops Lead      |
|                                |                  | interactive WhatsApp picker. Allocate chosen slot.          |                        |
+----------------------------------------------------------------------------------------------------------------------------------+
| 3. FACULTY_FORM_MISSING        | Unresolved (P1)  | Invoice paid > 2h with no teacher form. High scheduling     | 2 Hours                |
|                                |                  | risk. System pulls student profile from master roster;      | Ops Tier 1 / Teacher   |
|                                |                  | prompts teacher with 1-tap WhatsApp confirm button.         |                        |
+----------------------------------------------------------------------------------------------------------------------------------+
| 4. SCHOLARSHIP_APPROVAL_REQ    | Unresolved (P2)  | Teacher offered custom discount (e.g. 20% retention fee).   | 2 Hours                |
|                                |                  | Verify student tenure. Post approval card to Slack          | Head of Operations     |
|                                |                  | `#ops-approvals` for 1-click manager authorization.         |                        |
+----------------------------------------------------------------------------------------------------------------------------------+
| 5. PARTIAL_PAYMENT             | Unresolved (P1)  | Partial payment settled (e.g. INR 5,250 of INR 10,500).     | 4 Hours                |
|                                |                  | Hold scheduling. Generate dynamic payment link for remaining| Finance / Retention    |
|                                |                  | balance. Dispatch WhatsApp prompt to parent.                | Lead                   |
+----------------------------------------------------------------------------------------------------------------------------------+
| 6. PAYMENT_FAILED              | Unresolved (P0)  | Gateway status is Failed. Teacher submitted form on basis of| 15 Minutes             |
|                                |                  | screenshot. Reject submission immediately. Dispatch payment | Automated Gateway /    |
|                                |                  | retry link to parent. Alert teacher classes cannot start.   | Ops Tier 1             |
+----------------------------------------------------------------------------------------------------------------------------------+
| 7. BATCH_CHANGE_REQUIRED       | Unresolved (P2)  | Parent requested slot/day change (e.g. weekday to weekend). | 4 Hours                |
|                                |                  | Dispatch interactive WhatsApp slot selector showing open    | Parent Self-Service    |
|                                |                  | slots. Ops follows up if unselected after 12 hours.         | (Ops Tier 1 fallback)  |
+----------------------------------------------------------------------------------------------------------------------------------+
| 8. DUPLICATE_FORM (Identical)  | Resolved Warning | Form resubmitted due to browser freeze (e.g. Form 3309).    | Real-time (< 5 mins)   |
|                                |                  | System compares fields; auto-merges with canonical form     | Automated Engine       |
|                                |                  | 3308. Non-blocking warning logged; renewal auto-approved.   |                        |
+----------------------------------------------------------------------------------------------------------------------------------+
| 9. DUPLICATE_FORM (Conflicting)| Unresolved (P1)  | Duplicate submissions carry conflicting fees or batch times.| 2 Hours                |
|                                |                  | Block auto-approval. Escalate to Ops Tier 1 to contact      | Ops Tier 1             |
|                                |                  | teacher and clarify correct intent.                         |                        |
+----------------------------------------------------------------------------------------------------------------------------------+
| 10. INVOICE_ID_MISMATCH (Safe) | Resolved Warning | Teacher made typo (e.g. entered 84931 instead of 84913).    | Real-time (< 5 mins)   |
|                                |                  | Student profile has exactly 1 paid invoice. Auto-matched;   | Automated Engine       |
|                                |                  | non-blocking warning logged; renewal auto-approved.         |                        |
+----------------------------------------------------------------------------------------------------------------------------------+
| 11. INVOICE_ID_MISMATCH (Ambig)| Unresolved (P1)  | Invoice typo cannot be matched unambiguously (0 or >1 match)| 1 Hour                 |
|                                |                  | for student). Block auto-approval; escalate to Ops Tier 1.  | Ops Tier 1             |
+----------------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Roles & Responsibilities: RACI Matrix

To scale across **200+ teachers** with a **10-person Operations team**, team members must not perform manual transcription. Operations operates on an **exception-management model**:

### 4.1 Team Structure & Allocation (10-Person Team)
* **1 Operations Head (Process Owner):** Executive pipeline oversight, daily SLA compliance, policy approvals, high-tier escalations.
* **1 Operations Team Lead:** Shift management, queue triage, daily stand-up coordinator, P0/P1 exception escalation owner.
* **4 Tier-1 Operations Executives (Verification & Triage):** Responsible for phone mismatches, ambiguous invoice typos, teacher form nudges, and manual parent slot follow-ups.
* **2 Tier-2 Operations Executives (Batch & Academic Scheduling):** Responsible for batch capacity management, sister batch reassignments, educator allocation, and schedule adjustments.
* **1 Retention & Scholarship Specialist (Commercial Ops):** Handles discount authorisations, partial payment balance chasing, and retention escalations.
* **1 Systems & Automation Specialist (No-Code / Data Ops):** Manages webhook health, n8n orchestrator workflows, dashboard integrity, and audit logging.

### 4.2 RACI Matrix Across Pipeline Stages

```
+--------------------------------------------------------------------------------------------------------------------+
| Pipeline Activity              | Ops Head | Ops Lead | Ops T1 | Ops T2 | Teachers | Finance | Product | Parents    |
+--------------------------------------------------------------------------------------------------------------------+
| 1. Payment Gateway Ingestion   | I        | I        | I      | I      | I        | A       | R       | C          |
| 2. Zero-Touch Auto-Approval    | A        | I        | I      | I      | I        | I       | R       | I          |
| 3. Orphaned Invoice Follow-up  | A        | C        | R      | I      | R        | I       | I       | C          |
| 4. Contact Mismatch Resolution | A        | I        | R      | I      | C        | I       | I       | C          |
| 5. Partial Payment Chasing     | A        | I        | C      | I      | C        | R       | I       | R          |
| 6. Failed Payment Handling     | A        | I        | R      | I      | I        | C       | I       | R          |
| 7. Batch Capacity Allocation   | A        | C        | I      | R      | C        | I       | I       | C          |
| 8. Scholarship Sign-Off        | A / R    | C        | C      | I      | C        | C       | I       | I          |
| 9. Class Calendar Scheduling   | A        | I        | I      | R      | I        | I       | I       | I          |
| 10. Parent / Teacher Comms     | A        | I        | I      | I      | I        | I       | R       | R          |
+--------------------------------------------------------------------------------------------------------------------+
Legend: R = Responsible (Does the work), A = Accountable (Approver / Owner), C = Consulted (Provides input), I = Informed (Kept updated)
```

---

## 5. Operational SLAs & Escalation Matrix

All SLAs are defined as **proposed operational targets** to be benchmarked during pilot rollout:

```
+--------------------------------------------------------------------------------------------------------------------+
| Priority Level | Trigger Event                                  | Initial Action SLA | Max Resolution | Escalation  |
+--------------------------------------------------------------------------------------------------------------------+
| P0 (Critical)  | Payment failed at gateway, yet claimed by form | < 15 minutes       | 1 Hour         | Ops Lead    |
| P1 (High)      | Batch at 6/6 capacity; Paid invoice orphaned   | < 30 minutes       | 3 Hours        | Ops Lead    |
|                | > 2 hours; Partial payment uncollected         |                    |                |             |
| P2 (Medium)    | Contact phone mismatch; Batch change request;  | < 1 hour           | 4 Hours        | Tier 1 Lead |
|                | Custom discount pending manager approval       |                    |                |             |
| P3 (Low)       | Clean renewal auto-approval; Resolved warning  | < 5 minutes (Auto) | 15 Minutes     | Automated   |
+--------------------------------------------------------------------------------------------------------------------+
```

### Escalation Protocol:
1. **Breach Warning (50% SLA Elapsed):** Automated Slack ping to the assigned owner's channel (`#ops-triage`).
2. **First Escalation (75% SLA Elapsed):** Notification escalates to Ops Team Lead with student context and direct WhatsApp trigger.
3. **Executive Escalation (100% SLA Breached):** Highlighted in red on the Operations Head Daily Dashboard and reported during midday stand-up.
