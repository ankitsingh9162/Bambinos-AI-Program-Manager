# Bambinos.live — AI Program Manager Take-Home Assignment
## Re-Engineering & Automating the Student Renewal → Class Scheduling Pipeline

> **Role:** Senior AI Program Manager (Operations Excellence)  
> **Candidate Repository:** [https://github.com/ankitsingh9162/Bambinos-AI-Program-Manager](https://github.com/ankitsingh9162/Bambinos-AI-Program-Manager)  
> **Official Challenge:** [https://github.com/bambinoslive/AI-PM-hiring-take-home-assignments](https://github.com/bambinoslive/AI-PM-hiring-take-home-assignments)  
> **Submission Form:** [https://forms.gle/gu5gzySRHTSd5Uou9](https://forms.gle/gu5gzySRHTSd5Uou9)  

---

## Executive Overview

At **Bambinos.live**, delivering an exceptional customer journey requires that recurring revenue smoothly and immediately translates into reserved class seats. Historically, renewal operations operated across four siloed tabular datasets—invoices, faculty forms, booking requests, and class schedules—resulting in friction, scheduling delays, and operational blindspots.

This repository delivers a comprehensive, production-grade re-engineering and automation solution across four rigorous deliverables:
1. **Deliverable A:** Quantitative Leakage Funnel, Root Cause Analysis, and Operational KPI Baselines.
2. **Deliverable B:** AI & No-Code Workflow Architecture, Exception Handling Matrix, and Safeguard Governance.
3. **Deliverable C:** Python Reconciliation & Auto-Approval Engine, deterministic booking resolution, and automated notification generators.
4. **Deliverable D:** Operations Head Daily Dashboard (Streamlit), Operations SOP, Incident Playbook, Implementation Roadmap, and Risk Governance.

### Key Audited Operational Metrics (13-Student Cohort)

| Metric | Historical Baseline (CSV) | Reconciliation Engine Result | Status / Notes |
| :--- | :--- | :--- | :--- |
| **Total Invoices / Unique Students** | 13 records / 13 students | 13 records / 13 students | 100% accounted for |
| **Paid Invoices** | 11 (84.6% of cohort) | 11 validated paid | ₹1,55,500 total paid |
| **Partial / Failed Invoices** | 1 Partial (₹5,250) / 1 Failed | 1 Partial (68109) / 1 Failed (68111) | Blocked from auto-booking |
| **Auto-Approved Renewals** | 0 automated (1 scheduled) | **5 students (45.5% of Paid)** | Zero manual touch |
| **Unresolved Exceptions** | Not classified | **8 students (61.5% of cohort)** | Routed to designated human queues |
| **Resolved Warnings (No Overlap)** | Not handled | **2 students (68108, 68113)** | Safely resolved; 0 auto-approved overlap |
| **Existing Bookings Preserved** | 4 in CSV (`5501, 5502, 5505, 5512`) | **2 reused (`5501, 5502`)** | Deterministic preservation |
| **New Simulated Bookings** | N/A | **3 created (`5601, 5602, 5603`)** | Guaranteed collision-free range |
| **Drafted Communications** | 0 automated | **27 notification drafts** | Context-specific WhatsApp/Slack drafts |
| **Automated Test Suite** | 0 tests | **20 unit/integration tests** | **100% Passing (20/20)** |
| **End-to-End Scheduling SLA** | ~104.7 min single-record sample | **< 15 minutes** | Proposed operational target |

---

## Repository Structure

```text
AI-PM-hiring-take-home-assignments/
├── README.md                                  # Root documentation (this file)
├── ops/
│   ├── data/                                  # ORIGINAL UNMODIFIED CSV DATASETS
│   │   ├── Invoices-2026-03-30.csv            # 13 billing records (11 Paid, 1 Partial, 1 Failed)
│   │   ├── Faculty-Form-2026-03-30.csv        # 12 teacher renewal submission rows
│   │   ├── Booking-Requests-2026-03-30.csv    # 4 booking request records
│   │   ├── Class-Schedules-2026-03-30.csv     # 1 confirmed scheduled class record
│   │   └── Teachers-Capacity-2026-03-30.csv   # 6 teacher capacity & utilization profiles
│   ├── audit/                                 # DELIVERABLE A & B ARTIFACTS
│   │   ├── leakage_audit.csv                  # 13-row student-by-student funnel tracing
│   │   ├── root_cause_analysis.md             # Quantitative analysis of 7 operational failure modes
│   │   ├── operational_kpis.md                # 6 core KPI formulas, baselines, and targets
│   │   ├── workflow_architecture.md           # Proposed end-to-end zero-touch workflow
│   │   ├── exception_handling_matrix.csv      # 10 standardized routing reason codes
│   │   ├── workflow_diagram.mmd               # Mermaid sequence and state machine diagram
│   │   └── automation_safeguards.md           # Fallback, verification, and audit logs
│   ├── engine/                                # DELIVERABLE C PROTOTYPE
│   │   ├── reconciliation_engine.py           # Core Pandas reconciliation and auto-booking engine
│   │   ├── config.py                          # Configurable business thresholds and rule weights
│   │   ├── outputs/                           # Generated operational output artifacts
│   │   │   ├── auto_approved.csv              # 5 auto-approved students (68101, 68102, 68103, 68108, 68113)
│   │   │   ├── flagged_exceptions.csv         # 8 blocking exception students
│   │   │   ├── resolved_warnings.csv          # 2 non-blocking warnings (duplicate form, invoice typo)
│   │   │   ├── notification_drafts.csv        # 27 drafted outbound notifications
│   │   │   └── processing_summary.json        # Machine-readable reconciliation statistics
│   │   └── tests/
│   │       └── test_reconciliation.py         # 20 comprehensive unit and edge-case tests
│   ├── dashboard/                             # DELIVERABLE D OPS DASHBOARD
│   │   ├── app.py                             # Interactive Streamlit operations dashboard
│   │   └── requirements.txt                   # Dashboard dependencies (streamlit, pandas, plotly)
│   └── deliverable_d/                         # DELIVERABLE D GOVERNANCE & SOPS
│       ├── operations_sop.md                  # Standard Operating Procedure (Ops Head & Team)
│       ├── daily_operations_playbook.md       # Incident handling playbook for 8 exception types
│       ├── implementation_roadmap.md          # 30-60-90 day phased rollout plan & RACI
│       ├── kpi_dictionary.md                  # Comprehensive dictionary of 15 business metrics
│       ├── risks_and_dependencies.md          # Risk matrix, mitigations, and tech assumptions
│       └── README.md                          # Deliverable D overview and verification summary
└── submission/                                # SUBMISSION PACKAGE
    ├── Final_Bambinos_AI_Program_Manager_Report.pdf  # Comprehensive 11-page publication-grade PDF
    ├── generate_pdf_report.py                 # Automated ReportLab PDF generator
    └── SUBMISSION_CHECKLIST.md                # Submission verification checklist
```

---

## Deliverables Summary

### Deliverable A: Quantitative Leakage Funnel & Root Cause Analysis
- **Funnel Tracing:**
  - 13 Total Invoices → 11 Paid (84.6%), 1 Partial, 1 Failed.
  - 11 Unique Students with Faculty Forms (10 distinct forms + 1 browser double-click duplicate `3309` for Student `68108`).
  - 4 Historical Booking Requests (`5501, 5502, 5505, 5512`).
  - 1 Scheduled Class (`5501` for Student `68101`).
- **Root Cause Quantifications:**
  - **15.4% Payment Friction:** Student `68109` paid ₹5,250 of ₹10,500; Student `68111` failed payment.
  - **18.2% Paid Orphaned Invoice Rate:** Students `68106` (₹18,000) and `68110` (₹11,000) paid in full, but zero faculty forms were submitted.
  - **22.2% Capacity Bottleneck:** 2 out of 9 students requesting existing batches were blocked due to teacher saturation (`T101` at 6/6 and `T105` slot conflict).
  - **72.7% Booking Request Drop-off:** 8 out of 11 paid students had no booking request created under legacy manual operations.

### Deliverable B: AI & No-Code Re-Engineered Architecture
- **Zero-Touch Target Workflow:**
  - Integrates Webhook ingestion (`Razorpay/Stripe`), automated validation engine (`n8n / Python`), dynamic batch allocation (`PostgreSQL`), and multi-channel messaging (`WhatsApp / Slack`).
- **Standardized Exception Taxonomy (10 Reason Codes):**
  - `CODE_00` (Happy Path Auto-Approved).
  - `CODE_01` (Unpaid/Failed), `CODE_02` (Partial Payment), `CODE_03` (Paid Orphan / Missing Form).
  - `CODE_04` (Student/Parent Contact Mismatch), `CODE_05` (Batch Full / Max Capacity).
  - `CODE_06` (Slot Conflict / Slot Unavailable), `CODE_07` (Scholarship / Special Pricing Review).
  - `CODE_08` (Form Discrepancy / Typo Requiring Human Review), `CODE_09` (Duplicate Form Conflict).

### Deliverable C: Python Prototype Reconciliation Engine
- **Deterministic Student Dispositions:**
  - **5 Auto-Approved (45.5% of Paid Invoices):**
    - `68101`: Reused booking `5501`, slot confirmed with teacher `T101`.
    - `68102`: Reused booking `5502`, slot confirmed with teacher `T102`.
    - `68103`: Created new booking `5601`, allocated capacity in batch `B103`.
    - `68108`: Created new booking `5602`, merged identical form duplicate `3309` into `3308`.
    - `68113`: Created new booking `5603`, auto-corrected single-digit invoice typo `84931` → `84913`.
  - **8 Unresolved Exceptions (61.5% of Cohort):**
    - `68104`: Phone mismatch (Invoice `9876543213` vs Form `9876543299`).
    - `68105`: Batch capacity full (`T101` at 6/6 capacity limit).
    - `68106`: Missing faculty form (₹18,000 paid orphaned invoice).
    - `68107`: Fee mismatch / Scholarship applied (₹9,000 paid vs ₹10,500 standard).
    - `68109`: Partial payment (₹5,250 paid of ₹10,500).
    - `68110`: Missing faculty form (₹11,000 paid orphaned invoice).
    - `68111`: Payment failed (₹0 collected).
    - `68112`: Batch change requested (`B102` → `B108`, teacher `T105` unlisted).
  - **Zero Overlap:** Auto-approved list and flagged exceptions list share exactly 0 students ($5 + 8 = 13$).

### Deliverable D: Operations Dashboard & 30-60-90 Day Plan
- **Interactive Streamlit Dashboard:** Features 6 Executive KPI summary cards, filterable exception queues, simulated batch load distribution, and pre-formatted WhatsApp draft drawers.
- **Operations Governance:** Complete SOP with 15-minute SLA on exceptions, incident runbooks with scripted escalation trees, 30-60-90 day phased rollout plan, and a 15-metric KPI dictionary.

---

## Quickstart & Execution Guide

### Prerequisites
- Python 3.10+ installed.
- Required packages: `pandas`, `streamlit`, `plotly`, `reportlab`.

```bash
# Clone the repository
git clone https://github.com/ankitsingh9162/Bambinos-AI-Program-Manager.git
cd Bambinos-AI-Program-Manager

# Install dependencies
pip install pandas streamlit plotly reportlab
```

### 1. Execute the Reconciliation Engine
Run the core reconciliation prototype to ingest original CSVs and generate all output artifacts:
```bash
python ops/engine/reconciliation_engine.py
```
*Outputs will be refreshed in `ops/engine/outputs/`.*

### 2. Run the Automated Test Suite (20 Tests)
Execute the complete unit and integration test suite:
```bash
python -m unittest ops/engine/tests/test_reconciliation.py
```
*Expected result: `Ran 20 tests in ~0.05s - OK`.*

### 3. Launch the Operations Head Daily Dashboard
Start the local interactive Streamlit dashboard:
```bash
streamlit run ops/dashboard/app.py
```
*Open your web browser at `http://localhost:8501` to view live KPI cards, interactive tables, and communication draft drawers.*

### 4. Regenerate the Final PDF Report
Compile the comprehensive 11-page publication-quality PDF report:
```bash
python submission/generate_pdf_report.py
```
*The output PDF is saved at `submission/Final_Bambinos_AI_Program_Manager_Report.pdf`.*

---

## Operational Safeguards & Governance

1. **Financial Immutability:** The engine never approves bookings for `PARTIAL` or `FAILED` invoices. Financial reconciliation requires a confirmed webhook event from Razorpay/Stripe before triggering the engine.
2. **Zero In-Memory Collision Guarantee:** Existing booking request IDs (`5501`, `5502`) are preserved. Newly generated simulated bookings are allocated in the `5600+` range (`5601, 5602, 5603`), eliminating ID collisions.
3. **Audited Duplicate Form Handling:** Duplicate forms are compared across student, teacher, batch, and contact fields. Identical duplicate forms (e.g. `3308` & `3309`) are safely merged with an audit log; conflicting forms are blocked and routed for human review.
4. **Environment Isolation:** All communication drafts (WhatsApp / Slack) are generated as simulated draft payloads. No external API endpoints or real parent communications are dispatched without authenticated supervisor approval.

---

## License & Attribution
Prepared as part of the official Bambinos.live AI Program Manager (Operations Excellence) Take-Home Evaluation.  
All raw datasets in `ops/data/` remain the property of Bambinos.live.
