# Daily Operations Management Playbook

**Document Code:** PLY-OPS-REN-002  
**Role:** Senior AI Program Manager (Operations)  
**Organization:** Bambinos.live  
**Audience:** 10-Person Operations Team, Ops Team Lead, Head of Operations  
**Document Purpose:** Define the daily operational cadence, review checkpoints, triage protocols, and end-of-day reporting routines to ensure zero renewal backlogs and maintain strict SLA compliance.

---

## 1. Daily Operating Rhythm (Three-Checkpoint Rhythm)

To prevent renewal backlogs from compounding across live teaching cycles, the Operations team operates on a structured **Three-Checkpoint Rhythm**:

```
+---------------------------------------------------------------------------------------------------------+
|                                    DAILY THREE-CHECKPOINT RHYTHM                                        |
+---------------------------------------------------------------------------------------------------------+
|  1. MORNING CHECKPOINT (09:00 - 09:30 AM)  |  2. MIDDAY CHECKPOINT (02:00 - 02:30 PM)  |  3. EOD REVIEW (06:30 - 07:00 PM)  |
|  - Audit overnight paid invoices           |  - Review SLA breach warnings (> 2h)     |  - Verify all approved classes booked |
|  - Flag orphaned invoices > 2h             |  - Follow up on parent WhatsApp slot picks| - Review unresolved exception backlog|
|  - Review batch full exceptions            |  - Reconcile partial payment tranches    |  - Generate Ops Head Executive Digest |
|  - Assign Tier 1/2 ticket owners           |  - Process manager discount sign-offs    |  - Lock priority queue for tomorrow   |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. Checkpoint Execution Protocols

### Checkpoint 1: Morning Operations Review (09:00 AM – 09:30 AM)
* **Chair:** Operations Team Lead  
* **Attendees:** Entire 10-person Operations Team  
* **Dashboard View:** Streamlit / Retool Ops Head Daily Dashboard (KPI Cards & Exception Table)  
* **Mandatory Checklist:**
  1. **Overnight Paid Invoices:** Review all transactions settled between 06:00 PM yesterday and 09:00 AM today. Verify auto-approved renewals have generated active schedules.
  2. **Orphaned Invoice Audit:** Query `FACULTY_FORM_MISSING` exceptions. Identify any paid invoice > 2 hours without teacher submission. Instantly dispatch 1-tap WhatsApp prompt to the educator.
  3. **Capacity Ceiling Check:** Review batches flagged as `BATCH_FULL` (occupancy 6/6). Tier-2 academic coordinators check available seats in sister batches.
  4. **Queue Assignment:** Team Lead distributes unresolved exception cards across the 4 Tier-1 executives and assigns priority tags (P0, P1, P2).

---

### Checkpoint 2: Midday SLA & Escalation Stand-Up (02:00 PM – 02:30 PM)
* **Chair:** Operations Team Lead  
* **Attendees:** Tier-1 and Tier-2 Operations Executives, Retention Specialist  
* **Focus:** Preventing SLA breaches before the evening live class rush (04:00 PM – 08:00 PM)  
* **Mandatory Checklist:**
  1. **SLA Breach Warnings:** Inspect all open exceptions older than 2 hours.
  2. **Payment Failure Triage:** Verify `PAYMENT_FAILED` parent notifications. If a parent attempted UPI payment and failed, confirm whether a fresh retry link was opened.
  3. **Parent Slot Selection Chasing:** Follow up on `BATCH_CHANGE_REQUIRED` tickets where parents have not selected a slot via WhatsApp within 4 hours. Trigger outbound phone call if needed.
  4. **Discount Authorizations:** Ensure all `SCHOLARSHIP_APPROVAL_REQUIRED` cards in Slack `#ops-approvals` have been reviewed and approved/rejected by the Head of Operations.

---

### Checkpoint 3: End-of-Day Reconciliation & Sign-Off (06:30 PM – 07:00 PM)
* **Chair:** Head of Operations & Operations Team Lead  
* **Attendees:** Operations Team Lead, Data Ops Specialist  
* **Focus:** Queue clearance, daily reporting, and overnight readiness  
* **Mandatory Checklist:**
  1. **Zero Overnight Backlog Audit:** Confirm that 100% of clean renewals received before 05:00 PM are fully scheduled in `class_schedule_bookings`.
  2. **Exception Roll-Over Assessment:** Verify that no P0 or P1 exception remains unassigned or unattended.
  3. **Batch Roster Integrity:** Confirm that active batch occupancy numbers in reference tables accurately reflect day-end additions.
  4. **Dispatch Executive Digest:** Publish the standardized End-of-Day Summary to executive leadership.

---

## 3. Exception Triage & Ownership Routing Matrix

When an exception appears on the live dashboard, ownership is automatically assigned based on the Reason Code:

```
+--------------------------------------------------------------------------------------------------------------------+
| Reason Code                    | Severity | Primary Owner        | Secondary Escalation | Standard Action Protocol  |
+--------------------------------------------------------------------------------------------------------------------+
| PAYMENT_FAILED                 | P0       | Ops Tier 1           | Ops Team Lead        | Direct WhatsApp retry link|
| BATCH_FULL                     | P1       | Academic Ops T2      | Head of Operations   | Allocate sister batch slot|
| FACULTY_FORM_MISSING           | P1       | Ops Tier 1           | Teacher Coordinator  | 1-tap WhatsApp nudge      |
| PARTIAL_PAYMENT                | P1       | Retention Specialist | Finance Lead         | Tranche 2 balance link    |
| SCHOLARSHIP_APPROVAL_REQUIRED  | P2       | Head of Operations   | Chief Operating Off. | 1-click Slack card signoff|
| BATCH_CHANGE_REQUIRED          | P2       | Parent Self-Service  | Ops Tier 1           | Interactive slot picker   |
| PHONE_MISMATCH                 | P2       | Ops Tier 1           | Ops Team Lead        | Family user profile link  |
| DUPLICATE_FORM (Conflicting)   | P1       | Ops Tier 1           | Ops Team Lead        | Teacher verification call |
| INVOICE_ID_MISMATCH (Ambiguous)| P1       | Ops Tier 1           | Data Ops Specialist  | Manual database lookup    |
+--------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Standardized End-of-Day (EOD) Operations Report Template

Every evening at 07:00 PM, the Team Lead distributes the following standardized markdown report to the Head of Operations and COO via Slack channel `#ops-leadership`:

```markdown
### 📊 Bambinos.live Daily Renewal Operations Digest — [DATE]

**1. Executive Scorecard**
- Total Invoices Ingested Today: [XX] (Paid: [XX] | Partial: [XX] | Failed: [XX])
- Auto-Approved Renewals: [XX] ([XX.X]% of Paid Invoices)
- Existing Bookings Reused: [XX] | New Bookings Created: [XX]
- Unresolved Exceptions Flagged: [XX]
- Exceptions Resolved Today: [XX]
- Overnight Pending Backlog: [XX] (Target: 0)

**2. Exception Resolution Breakdown**
- `FACULTY_FORM_MISSING`: [X] received -> [X] resolved via teacher 1-tap nudge
- `BATCH_FULL`: [X] received -> [X] allocated to sister batches
- `PHONE_MISMATCH`: [X] received -> [X] verified via family profile
- `PARTIAL_PAYMENT`: [X] received -> INR [XX,XXX] outstanding balance chased
- `SCHOLARSHIP_APPROVAL_REQUIRED`: [X] discount approvals completed

**3. Batch Capacity Highlights**
- Batches at 6/6 Capacity: [List Batch IDs]
- New Batch Openings Recommended: [Grade/Course]

**4. Critical Escalations & Next-Day Focus**
- [Highlight any blocked student requiring Head of Ops attention]
- Signed off by: [Ops Team Lead Name]
```
