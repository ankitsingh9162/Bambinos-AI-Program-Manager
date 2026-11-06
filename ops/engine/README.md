# Bambinos.live Renewal Reconciliation & Auto-Approval Engine

**Role:** AI Program Manager (Operations)  
**Deliverable C:** Working Prototype (Reconciliation & Auto-Approval Engine)  
**Technology:** Python 3.10+ / Pandas / Unittest  

---

## 1. Overview & Business Purpose

This directory contains the working prototype of the **Zero-Touch Student Renewal & Exception Handling Engine** for Bambinos.live. 

The engine replaces manual data transcription across disparate spreadsheets with a deterministic, rule-based reconciliation pipeline. It validates financial ground truth against payment gateway transactions, auto-approves clean recurring renewals into live batches without human Ops delay, separates **unresolved blocking exceptions** from **auto-resolved warnings**, distinguishes between reused existing bookings and newly created bookings, and drafts personalized WhatsApp/Slack notification templates for parents, teachers, and Ops executives.

---

## 2. Directory Structure

```
ops/engine/
│
├── config.py                  # Configurable thresholds, paths, and 10 standardized reason codes
├── reconciliation_engine.py   # Core deterministic reconciliation and auto-approval engine
│
├── outputs/                   # Generated prototype deliverables (Preserves original data)
│   ├── auto_approved.csv      # Clean renewals qualified for automated scheduling (5 records)
│   ├── flagged_exceptions.csv # Unresolved blocking exceptions requiring triage/review (8 records)
│   ├── resolved_warnings.csv  # Non-blocking warnings automatically resolved by the engine (2 records)
│   ├── notification_drafts.csv# Drafted WhatsApp & Slack messages for parents & teachers (27 records)
│   └── processing_summary.json# Quantitative pipeline metrics, booking reuse counts, and reason-code distribution
│
├── tests/
│   └── test_reconciliation.py# Comprehensive unit and integration test suite (20 test cases)
│
└── README.md                  # System architecture, execution guide, and known limitations
```

---

## 3. Step-by-Step Processing Logic

The engine executes in 5 sequential stages:

```
[1. INGESTION] -> Loads all 5 CSVs from ops/data/ in read-only mode.
       │
[2. FORM RECONCILIATION & RESOLUTION]
       ├── Deduplication: Enforces composite key (student_id, invoice_id).
       │     - Identical duplicates (e.g. Form 3309) are classified as non-blocking RESOLVED WARNINGS.
       │     - Conflicting duplicates are classified as blocking UNRESOLVED EXCEPTIONS for human review.
       ├── Invoice Typo Handling: 
       │     - Unambiguous typos (e.g. Form 3313 matching single student invoice 84913) are auto-resolved as RESOLVED WARNINGS.
       │     - Ambiguous typos (0 or >1 matches) are classified as blocking UNRESOLVED EXCEPTIONS for human review.
       ├── Financial Ground Truth Check: 
       │     - Rejects Failed payments (e.g. Form 3311 / Invoice 84911) -> UNRESOLVED EXCEPTION.
       │     - Halts Partial payments (e.g. Form 3310 / Invoice 84909) -> UNRESOLVED EXCEPTION.
       ├── Identity Check: Flags payer phone != registered mobile (e.g. Form 3304) -> UNRESOLVED EXCEPTION.
       ├── Authorization Check: Flags custom discounts/scholarships (e.g. Form 3307) -> UNRESOLVED EXCEPTION.
       ├── Batch Capacity Check: Blocks renewals if active_students >= max_batch_size (e.g. Form 3305) -> UNRESOLVED EXCEPTION.
       ├── Batch Change Check: Routes slot change requests to self-service picker (e.g. Form 3312) -> UNRESOLVED EXCEPTION.
       └── Happy Path Auto-Approval & Idempotency: 
             - Approves clean renewals with capacity (Students 68101, 68102, 68103, 68108, 68113).
             - Reuses existing bookings (e.g. 5501 Completed, 5502 Pending) without creating duplicates.
             - Creates new simulated bookings only for renewals lacking existing booking requests.
       │
[3. ORPHANED INVOICE DETECTION]
       └── Scans for Paid invoices with NO teacher submission > 2h (Invoices 84906, 84910) -> UNRESOLVED EXCEPTIONS.
       │
[4. NOTIFICATION DRAFTING]
       └── Generates role-tailored WhatsApp/Slack copy with dynamic parameters for Parents and Teachers.
       │
[5. METRIC COMPILATION & EXPORT]
       └── Outputs structured CSVs and JSON summary without mutating source data.
```

---

## 4. Empirical Output Breakdown (Production Dataset Results)

When evaluated against the 13 invoices and 12 faculty form submissions in `ops/data/`, the engine produces:

* **Unique Invoices Processed:** **13** (11 Paid, 1 Partially_Paid, 1 Failed)
* **Unique Students Processed:** **13**
* **Unique Auto-Approved Renewals:** **5 renewals** (`68101`, `68102`, `68103`, `68108`, `68113`)
* **Existing Bookings Reused:** **2** (Booking `5501` for Student `68101` and Booking `5502` for Student `68102`)
* **New Bookings Created:** **3** (Simulated bookings for Students `68103`, `68108`, `68113`)
* **Unique Students with Unresolved Exceptions:** **8 students** (`68104`, `68105`, `68106`, `68107`, `68109`, `68110`, `68111`, `68112`)
* **Total Unresolved Exception Records:** **8 records** (7 human review cases + 1 parent self-service slot picker)
* **Resolved Warning Records:** **2 records** (Student `68108` duplicate form and Student `68113` invoice typo)
* **Overlap Between Auto-Approved and Unresolved:** **0 students** (Strict mathematical partition: $5 + 8 = 13$).
* **Notification Drafts Generated:** **27 drafts** (tailored message copy for Parents, Teachers, and Ops leads).

---

## 5. Execution & Testing Instructions

### Run the Reconciliation Engine:
```bash
python ops/engine/reconciliation_engine.py
```

### Run the Complete Test Suite (20 Tests):
```bash
python -m unittest ops/engine/tests/test_reconciliation.py
```
*Test suite status:* **20 tests passed, 0 failures (Ran in 0.135s)**.

---

## 6. Known Assumptions & Limitations

1. **Simulation Mode:** The prototype runs with `SIMULATION_MODE = True`. It generates proposed booking and schedule objects into `outputs/` without writing directly to the source database tables.
2. **Notification Channel:** Messages are saved as structured drafts in `notification_drafts.csv`. In production, these drafts would be dispatched via the Meta WhatsApp Cloud API and Slack Webhooks.
3. **Batch Capacity:** Batch size is evaluated against `reference_active_batches_and_students.csv` (`max_batch_size = 6`). Over-enrollment exceptions (`BATCH_FULL`) trigger when `active_students_count >= max_batch_size`.
4. **Deterministic LLM Boundaries:** The engine is 100% deterministic code. LLMs are not used for financial settlement, payment verification, or batch allocation decisions.
