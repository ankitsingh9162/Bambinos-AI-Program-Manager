"""
Configuration and Threshold Settings for Bambinos.live Renewal Engine
Deliverable C: Working Prototype
"""
import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

# Dataset File Names
INVOICES_FILE = "1_invoices.csv"
FACULTY_FORM_FILE = "2_faculty_form_unapproved.csv"
BOOKING_REQUESTS_FILE = "3_booking_requests.csv"
SCHEDULE_BOOKINGS_FILE = "4_class_schedule_bookings.csv"
REFERENCE_FILE = "reference_active_batches_and_students.csv"

# Output File Names
AUTO_APPROVED_FILE = os.path.join(OUTPUTS_DIR, "auto_approved.csv")
FLAGGED_EXCEPTIONS_FILE = os.path.join(OUTPUTS_DIR, "flagged_exceptions.csv")
RESOLVED_WARNINGS_FILE = os.path.join(OUTPUTS_DIR, "resolved_warnings.csv")
NOTIFICATION_DRAFTS_FILE = os.path.join(OUTPUTS_DIR, "notification_drafts.csv")
PROCESSING_SUMMARY_FILE = os.path.join(OUTPUTS_DIR, "processing_summary.json")

# Standardized Reason Codes (Deliverable B Taxonomy)
REASON_CODES = {
    "HAPPY_PATH": "HAPPY_PATH_AUTO_APPROVED",
    "MISSING_FORM": "FACULTY_FORM_MISSING",
    "PHONE_MISMATCH": "PHONE_MISMATCH",
    "PARTIAL_PAYMENT": "PARTIAL_PAYMENT",
    "PAYMENT_FAILED": "PAYMENT_FAILED",
    "INVOICE_TYPO": "INVOICE_ID_MISMATCH",
    "DUPLICATE_FORM": "DUPLICATE_FORM",
    "BATCH_FULL": "BATCH_FULL",
    "BATCH_CHANGE": "BATCH_CHANGE_REQUIRED",
    "SCHOLARSHIP": "SCHOLARSHIP_APPROVAL_REQUIRED"
}

# Operational Thresholds (Dataset-observed & configurable)
DEFAULT_MAX_BATCH_SIZE = 6
DEFAULT_TERM_SESSIONS = 24
ORPHANED_INVOICE_THRESHOLD_HOURS = 2.0
MAX_AUTONOMOUS_DISCOUNT_PERCENT = 0.0  # Discounts require approval

# Mode Setting
SIMULATION_MODE = True  # Distinguish simulated approvals from real production database writes
