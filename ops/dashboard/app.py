"""
Streamlit Operations Head Daily Dashboard
Bambinos.live Renewal-to-Class-Scheduling Pipeline
Deliverable D - Interactive Prototype
"""

import os
import json
import pandas as pd
import streamlit as st

# Configure Page
st.set_page_config(
    page_title="Bambinos.live | Ops Head Renewal Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 26px; font-weight: 700; color: #1E3A8A; margin-bottom: 2px; }
    .sub-header { font-size: 14px; color: #64748B; margin-bottom: 20px; }
    .kpi-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; margin-bottom: 10px; }
    .kpi-title { font-size: 13px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #0F172A; margin: 4px 0; }
    .kpi-subtitle { font-size: 12px; color: #64748B; }
    .badge-paid { background-color: #DCFCE7; color: #166534; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
    .badge-warn { background-color: #FEF9C3; color: #854D0E; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
    .badge-error { background-color: #FEE2E2; color: #991B1B; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Data Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ENGINE_DIR = os.path.join(PROJECT_ROOT, "engine")
OUTPUTS_DIR = os.path.join(ENGINE_DIR, "outputs")

@st.cache_data
def load_all_data():
    invoices = pd.read_csv(os.path.join(DATA_DIR, "1_invoices.csv"))
    faculty = pd.read_csv(os.path.join(DATA_DIR, "2_faculty_form_unapproved.csv"))
    bookings = pd.read_csv(os.path.join(DATA_DIR, "3_booking_requests.csv"))
    schedules = pd.read_csv(os.path.join(DATA_DIR, "4_class_schedule_bookings.csv"))
    reference = pd.read_csv(os.path.join(DATA_DIR, "reference_active_batches_and_students.csv"))
    
    auto_approved = pd.read_csv(os.path.join(OUTPUTS_DIR, "auto_approved.csv"))
    flagged_exceptions = pd.read_csv(os.path.join(OUTPUTS_DIR, "flagged_exceptions.csv"))
    resolved_warnings = pd.read_csv(os.path.join(OUTPUTS_DIR, "resolved_warnings.csv"))
    notifications = pd.read_csv(os.path.join(OUTPUTS_DIR, "notification_drafts.csv"))
    
    with open(os.path.join(OUTPUTS_DIR, "processing_summary.json")) as f:
        summary = json.load(f)
        
    return invoices, faculty, bookings, schedules, reference, auto_approved, flagged_exceptions, resolved_warnings, notifications, summary

invoices, faculty, bookings, schedules, reference, auto_approved, flagged_exceptions, resolved_warnings, notifications, summary = load_all_data()

# Header Banner
st.markdown('<div class="main-header">🎓 Bambinos.live — Operations Head Daily Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Student Renewal → Class Scheduling Pipeline • Daily Executive Control Center</div>', unsafe_allow_html=True)
st.info("ℹ️ **Prototype Dashboard — Sample Dataset Snapshot**: This dashboard displays processed records from the 13-student renewal cohort in `ops/data/` using the Deliverable C Reconciliation Engine. Figures reflect prototype simulation results.")

# ==============================================================================
# SECTION 1: EXECUTIVE KPI CARDS
# ==============================================================================
res = summary["reconciliation_results"]
inp = summary["input_dataset_counts"]

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(label="Total Unique Invoiced", value=inp["unique_students_processed"], delta="13 Invoices Received")
with c2:
    st.metric(label="Paid Invoices", value=inp["paid_invoices"], delta="84.6% Settle Rate")
with c3:
    st.metric(label="Auto-Approved Renewals", value=res["unique_renewals_auto_approved"], delta=f"{res['proposed_auto_approval_yield_pct']}% Paid Yield", delta_color="normal")
with c4:
    st.metric(label="Unresolved Exceptions", value=res["unique_students_with_unresolved_exceptions"], delta=f"{res['human_review_cases_count']} Require Human Review", delta_color="inverse")

c5, c6, c7, c8 = st.columns(4)
with c5:
    st.metric(label="Resolved Warnings", value=res["resolved_warnings_count"], delta="Deduplicated / Auto-corrected")
with c6:
    st.metric(label="New Bookings Created", value=res["new_bookings_created"], delta="Simulated Allocation")
with c7:
    st.metric(label="Existing Bookings Reused", value=res["existing_bookings_reused"], delta="Zero Duplication")
with c8:
    st.metric(label="Notification Drafts", value=res["total_notification_drafts_generated"], delta="WhatsApp & Slack Drafts")

st.markdown("---")

# ==============================================================================
# SECTION 2: SIDEBAR FILTERS
# ==============================================================================
st.sidebar.header("🔍 Pipeline Filters")
filter_status = st.sidebar.multiselect(
    "Filter Payment Status",
    options=["Paid", "Partially_Paid", "Failed"],
    default=["Paid", "Partially_Paid", "Failed"]
)

all_reasons = list(auto_approved["reason_code"].unique()) + list(flagged_exceptions["reason_code"].unique()) + list(resolved_warnings["reason_code"].unique())
all_reasons = sorted(list(set(all_reasons)))
filter_reason = st.sidebar.multiselect(
    "Filter Reason Code",
    options=all_reasons,
    default=all_reasons
)

all_batches = sorted(list(reference["current_classbatch_id"].unique()))
filter_batch = st.sidebar.multiselect(
    "Filter Batch ID",
    options=all_batches,
    default=all_batches
)

st.sidebar.markdown("---")
st.sidebar.caption("🔧 **Operating Mode**: Simulation Mode (Read-Only)\n\n📌 **Cohort Base**: 13 Students\n\n🎯 **Auto-Approval Target**: >= 80%\n\n⏱️ **Happy-Path TAT Target**: < 15 mins")

# ==============================================================================
# SECTION 3: VISUALIZATIONS & CHARTS
# ==============================================================================
tab_charts, tab_actions, tab_batches, tab_notifs = st.tabs(["📊 Funnel & Analytics", "📋 Daily Action Table", "🏫 Batch Capacity Roster", "💬 Notification Drafts"])

with tab_charts:
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("A. Renewal Pipeline Funnel")
        funnel_data = pd.DataFrame({
            "Stage": [
                "1. Total Invoices Received",
                "2. Successfully Paid Invoices",
                "3. Auto-Approved (Zero-Touch)",
                "4. Existing Bookings Reused",
                "5. New Bookings Created",
                "6. Unresolved Exceptions"
            ],
            "Count": [
                inp["unique_invoices_processed"],
                inp["paid_invoices"],
                res["unique_renewals_auto_approved"],
                res["existing_bookings_reused"],
                res["new_bookings_created"],
                res["unique_students_with_unresolved_exceptions"]
            ]
        })
        st.bar_chart(funnel_data.set_index("Stage"))
        st.caption("Note: Stages 4 and 5 represent mutually exclusive fulfillment paths that comprise Stage 3 (Auto-Approved). Stage 6 represents renewals held for exception triage.")

    with col_chart2:
        st.subheader("B. Unresolved Exceptions Breakdown")
        unresolved_dist = summary["reason_code_distribution"]["unresolved_exceptions"]
        df_exc = pd.DataFrame(list(unresolved_dist.items()), columns=["Reason Code", "Count"]).sort_values("Count", ascending=False)
        st.bar_chart(df_exc.set_index("Reason Code"))
        st.caption("All 8 unresolved records are blocked from scheduling until resolved by the designated owner.")

    col_pie1, col_pie2 = st.columns(2)
    with col_pie1:
        st.subheader("C. Payment Status Distribution")
        pay_df = pd.DataFrame({
            "Status": ["Paid", "Partially Paid", "Failed"],
            "Count": [inp["paid_invoices"], inp["partially_paid_invoices"], inp["failed_invoices"]]
        })
        st.dataframe(pay_df, use_container_width=True, hide_index=True)

    with col_pie2:
        st.subheader("D. Renewal Pipeline Status Distribution")
        status_df = pd.DataFrame({
            "Category": ["Auto-Approved Renewals", "Unresolved Blocking Exceptions", "Resolved Non-Blocking Warnings*"],
            "Unique Students / Records": [5, 8, 2],
            "Operational Impact": [
                "Auto-scheduled into live batches without Ops touchpoints",
                "Held in Ops exception queues; human review or parent action required",
                "*Separately logged warnings for students 68108 & 68113; both approved"
            ]
        })
        st.dataframe(status_df, use_container_width=True, hide_index=True)

# ==============================================================================
# SECTION 4: DAILY ACTION TABLE
# ==============================================================================
with tab_actions:
    st.subheader("E. Daily Operations Action Table (Cohort of 13 Students)")
    st.markdown("This table provides the daily queue of all 13 renewal cases, distinguishing auto-approved entries from prioritized unresolved exceptions.")

    # Reconstruct student action rows
    action_rows = []
    
    # 1. Auto-Approved (5 students)
    for _, r in auto_approved.iterrows():
        s_id = int(r["student_id"])
        inv_id = int(r["invoice_id"])
        action_rows.append({
            "Student ID": s_id,
            "Invoice ID": inv_id,
            "Payment Status": "Paid",
            "Pipeline Status": "AUTO_APPROVED",
            "Reason Code": "HAPPY_PATH_AUTO_APPROVED",
            "Next Required Action": f"Classes confirmed in Batch {r['allocated_classbatch_id']} ({r['booking_action']}). Send WhatsApp confirmation.",
            "Responsible Owner": "Automated Zero-Touch Engine",
            "Priority": "P3 (Low - Completed)",
            "Target SLA": "< 15 mins"
        })

    # 2. Unresolved Exceptions (8 students)
    priority_map = {
        "PAYMENT_FAILED": "P0 (Critical)",
        "FACULTY_FORM_MISSING": "P1 (High)",
        "PARTIAL_PAYMENT": "P1 (High)",
        "BATCH_FULL": "P1 (High)",
        "SCHOLARSHIP_APPROVAL_REQUIRED": "P2 (Medium)",
        "BATCH_CHANGE_REQUIRED": "P2 (Medium)",
        "PHONE_MISMATCH": "P2 (Medium)"
    }
    
    owner_map = {
        "PAYMENT_FAILED": "Automated Gateway Triage / Ops Tier 1",
        "FACULTY_FORM_MISSING": "Ops Tier 1 / Assigned Teacher",
        "PARTIAL_PAYMENT": "Finance / Retention Lead",
        "BATCH_FULL": "Academic Ops Lead / Batch Scheduler",
        "SCHOLARSHIP_APPROVAL_REQUIRED": "Head of Operations / Retention Lead",
        "BATCH_CHANGE_REQUIRED": "Parent Self-Service (Ops Tier 1 fallback)",
        "PHONE_MISMATCH": "Ops Tier 1 (Verification Agent)"
    }

    sla_map = {
        "PAYMENT_FAILED": "< 15 mins",
        "FACULTY_FORM_MISSING": "< 2 hours",
        "PARTIAL_PAYMENT": "< 4 hours",
        "BATCH_FULL": "< 3 hours",
        "SCHOLARSHIP_APPROVAL_REQUIRED": "< 2 hours",
        "BATCH_CHANGE_REQUIRED": "< 4 hours",
        "PHONE_MISMATCH": "< 2 hours"
    }

    action_map = {
        "PAYMENT_FAILED": "Payment failed at gateway. Do not schedule. Dispatch payment retry link to parent.",
        "FACULTY_FORM_MISSING": "Parent paid, but teacher omitted form. Prompt teacher via 1-tap WhatsApp alert.",
        "PARTIAL_PAYMENT": "Net paid INR 5,250 out of 10,500. Issue second tranche payment link.",
        "BATCH_FULL": "Target batch 9205 is 6/6 full. Present 2 sister batch options to parent.",
        "SCHOLARSHIP_APPROVAL_REQUIRED": "20% retention discount applied. Submit approval card in Slack #ops-approvals.",
        "BATCH_CHANGE_REQUIRED": "Parent requested weekend slot. Dispatch interactive WhatsApp slot picker.",
        "PHONE_MISMATCH": "Payer mobile differs from registered mobile. Verify family relation in Ops console."
    }

    for _, r in flagged_exceptions.iterrows():
        s_id = int(r["student_id"])
        inv_id = int(r["invoice_id"])
        code = r["reason_code"]
        inv_status = invoices[invoices["id"] == inv_id]["payment_status"].values[0] if len(invoices[invoices["id"] == inv_id]) > 0 else "Unknown"
        
        action_rows.append({
            "Student ID": s_id,
            "Invoice ID": inv_id,
            "Payment Status": inv_status,
            "Pipeline Status": "FLAGGED_FOR_TRIAGE",
            "Reason Code": code,
            "Next Required Action": action_map.get(code, r["description"]),
            "Responsible Owner": owner_map.get(code, r["assigned_owner"]),
            "Priority": priority_map.get(code, "P2 (Medium)"),
            "Target SLA": sla_map.get(code, "< 4 hours")
        })

    df_actions = pd.DataFrame(action_rows)

    # Apply Sidebar Filters
    df_filtered = df_actions[
        df_actions["Payment Status"].isin(filter_status) &
        df_actions["Reason Code"].isin(filter_reason)
    ]

    st.dataframe(df_filtered.sort_values("Priority"), use_container_width=True, hide_index=True)
    st.caption("Showing 13 distinct students. Auto-approved students have 0 unresolved blocking exceptions.")

# ==============================================================================
# SECTION 5: BATCH CAPACITY MONITORING
# ==============================================================================
with tab_batches:
    st.subheader("F. Live Batch Capacity Monitoring (Reference Active Batches)")
    st.markdown("Real-time occupancy tracking across active student batches. Enforces the dataset-observed capacity limit of 6 students per batch.")

    batch_display = []
    # Deduplicate batch level data
    unique_batches = reference.drop_duplicates(subset=["current_classbatch_id"])
    for _, b in unique_batches.iterrows():
        b_id = int(b["current_classbatch_id"])
        curr = int(b["active_students_count"])
        max_c = int(b["max_batch_size"])
        avail = max_c - curr
        
        if avail == 0:
            status = "🔴 FULL (Capacity Reached)"
        elif avail == 1:
            status = "🟡 NEAR FULL (1 Seat Left)"
        else:
            status = "🟢 AVAILABLE"

        batch_display.append({
            "Batch ID": b_id,
            "Batch Name": b["classbatch_name"],
            "Course / Grade": b["class_name"],
            "Days & Time": f"{b['batch_days']} {b['batch_start_time']}",
            "Educator Name": b["educator_name"],
            "Occupancy": f"{curr} / {max_c}",
            "Available Seats": avail,
            "Capacity Status": status
        })

    df_batch_display = pd.DataFrame(batch_display)
    df_batch_filtered = df_batch_display[df_batch_display["Batch ID"].isin(filter_batch)]
    st.dataframe(df_batch_filtered, use_container_width=True, hide_index=True)
    st.caption("Batch 9205 (CM-G4-Batch-D) is currently at maximum capacity (6/6). Renewing students for this batch are automatically routed to sister batches.")

# ==============================================================================
# SECTION 6: NOTIFICATION DRAFTS
# ==============================================================================
with tab_notifs:
    st.subheader("G. Pre-Generated Notification Drafts (WhatsApp & Slack)")
    st.markdown("All 27 notification drafts generated by the Deliverable C engine. Messages include dynamic student names, batch schedules, payment links, and escalation alerts.")
    st.dataframe(notifications[["recipient_role", "channel", "student_id", "invoice_id", "reason_code", "message_draft"]], use_container_width=True, hide_index=True)
    st.caption("Drafts only — no messages have been dispatched. Ready for WhatsApp Cloud API & Slack Webhook integration.")
