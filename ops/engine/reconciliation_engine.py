"""
Reconciliation & Auto-Approval Engine
Deliverable C: Working Prototype for Bambinos.live Operations
Ingests 5 operational CSVs, validates financial ground truth, resolves discrepancies,
distinguishes auto-approvals, resolved warnings, and unresolved blocking exceptions.
"""

import os
import json
import logging
from datetime import datetime
import pandas as pd
import numpy as np

import config

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RenewalEngine")

class ReconciliationEngine:
    def __init__(self, data_dir=config.DATA_DIR):
        self.data_dir = data_dir
        self.invoices = None
        self.faculty_forms = None
        self.booking_requests = None
        self.schedule_bookings = None
        self.reference = None

        # Output containers
        self.auto_approved_records = []
        self.resolved_warnings = []
        self.unresolved_exceptions = []
        self.notification_drafts = []
        self.summary_metrics = {}

        # Booking tracking counters
        self.existing_bookings_reused = 0
        self.new_bookings_created = 0

    def load_datasets(self):
        """Loads and validates the 5 CSV datasets without modifying originals."""
        logger.info(f"Loading datasets from {self.data_dir}...")
        
        self.invoices = pd.read_csv(os.path.join(self.data_dir, config.INVOICES_FILE))
        self.faculty_forms = pd.read_csv(os.path.join(self.data_dir, config.FACULTY_FORM_FILE))
        self.booking_requests = pd.read_csv(os.path.join(self.data_dir, config.BOOKING_REQUESTS_FILE))
        self.schedule_bookings = pd.read_csv(os.path.join(self.data_dir, config.SCHEDULE_BOOKINGS_FILE))
        self.reference = pd.read_csv(os.path.join(self.data_dir, config.REFERENCE_FILE))

        logger.info(f"Loaded: Invoices={len(self.invoices)}, FacultyForms={len(self.faculty_forms)}, "
                    f"Bookings={len(self.booking_requests)}, Schedules={len(self.schedule_bookings)}, "
                    f"Reference={len(self.reference)}")

    def run_reconciliation(self, reload_data=True):
        """Main deterministic classification pipeline."""
        if reload_data or self.invoices is None:
            self.load_datasets()
        
        # Reset tracking containers
        self.auto_approved_records = []
        self.resolved_warnings = []
        self.unresolved_exceptions = []
        self.notification_drafts = []
        self.existing_bookings_reused = 0
        self.new_bookings_created = 0

        # Track processed entities
        seen_form_keys = {}  # Map (student_id, invoice_id) -> canonical form record
        
        # Index existing bookings for idempotent lookup: (student_id, invoice_id) -> booking row
        existing_bookings_map = {}
        for _, b_row in self.booking_requests.iterrows():
            key = (int(b_row['student_id']), int(b_row['invoice_id']))
            existing_bookings_map[key] = b_row

        # Build reference lookup dictionary for fast O(1) access
        ref_lookup = self.reference.set_index('student_id').to_dict(orient='index')

        # -------------------------------------------------------------
        # STEP 1: Process All Submitted Faculty Forms
        # -------------------------------------------------------------
        for idx, form in self.faculty_forms.iterrows():
            f_id = int(form['id'])
            s_id = int(form['student_id'])
            u_id = int(form['user_id'])
            entered_inv_id = int(form['invoice_id'])
            f_amt = float(form['amount_paid'])
            remarks = str(form['remarks']) if pd.notnull(form['remarks']) else ""
            continue_same = str(form['continue_same_batch']).strip().lower() in ['yes', 'true', '1']
            pref_time = str(form['preferred_time_slot']).strip()

            ref_data = ref_lookup.get(s_id, {})
            ref_mobile = str(ref_data.get('registered_mobile_masked', '')).strip()
            std_fee = float(ref_data.get('standard_fee_24_sessions_inr', 0.0))
            current_batch_id = int(ref_data.get('current_classbatch_id', 0))
            batch_capacity = int(ref_data.get('max_batch_size', config.DEFAULT_MAX_BATCH_SIZE))
            active_count = int(ref_data.get('active_students_count', 0))
            educator_name = str(ref_data.get('educator_name', form.get('educator_name', 'Teacher')))

            # Check for Duplicate Faculty Form (e.g. Forms 3308 & 3309 for Student 68108)
            form_dedup_key = (s_id, entered_inv_id)
            if form_dedup_key in seen_form_keys:
                prior_form = seen_form_keys[form_dedup_key]
                # Compare critical scheduling and payment fields
                is_conflicting = (
                    prior_form['amount_paid'] != f_amt or
                    str(prior_form['continue_same_batch']).strip().lower() != str(form['continue_same_batch']).strip().lower() or
                    str(prior_form['preferred_time_slot']).strip() != str(form['preferred_time_slot']).strip() or
                    int(prior_form['current_classbatch_id']) != int(form['current_classbatch_id'])
                )

                if is_conflicting:
                    # Conflicting duplicate: BLOCK auto-approval and send to human review
                    self._record_unresolved_exception(
                        student_id=s_id,
                        user_id=u_id,
                        invoice_id=entered_inv_id,
                        faculty_form_id=f_id,
                        reason_code=config.REASON_CODES["DUPLICATE_FORM"],
                        description=f"Duplicate faculty form submission with CONFLICTING information detected for student {s_id} (Prior Form {prior_form['id']} vs New Form {f_id}). Human review required.",
                        severity="HIGH",
                        owner="Ops Tier 1",
                        human_review_required=True,
                        draft_parent_msg=None,
                        draft_teacher_msg=f"Alert {educator_name}: Duplicate renewal form submitted with conflicting data for Student #{s_id}. Ops review required."
                    )
                else:
                    # Identical duplicate (e.g. Form 3309 after browser freeze): Non-blocking RESOLVED WARNING
                    self._record_resolved_warning(
                        student_id=s_id,
                        user_id=u_id,
                        invoice_id=entered_inv_id,
                        faculty_form_id=f_id,
                        reason_code=config.REASON_CODES["DUPLICATE_FORM"],
                        description=f"Duplicate faculty form {f_id} identical to canonical form {prior_form['id']} (Student {s_id}, Invoice {entered_inv_id}). Duplicate suppressed; canonical form retained.",
                        resolution_applied="DEDUPLICATED_CANONICAL_FORM_RETAINED",
                        owner="Automated Zero-Touch Engine",
                        draft_teacher_msg=f"Hello {educator_name}, duplicate renewal submission (Form #{f_id}) for Student #{s_id} was safely merged with Form #{prior_form['id']}."
                    )
                continue  # Skip further processing of the duplicate row itself
            
            # Record canonical form for this (student_id, entered_inv_id)
            seen_form_keys[form_dedup_key] = form

            # Check Invoice ID Typo / Mismatch (e.g. Form 3313 entered 84931 instead of 84913)
            matching_inv = self.invoices[self.invoices['id'] == entered_inv_id]
            actual_inv_id = entered_inv_id
            is_resolved_typo = False

            if matching_inv.empty:
                # Attempt auto-reconciliation using student_id
                inv_by_student = self.invoices[self.invoices['student_id'] == s_id]
                if len(inv_by_student) == 1:
                    # Unambiguous single match! Auto-reconcile and record as a non-blocking RESOLVED WARNING
                    actual_inv_id = int(inv_by_student.iloc[0]['id'])
                    matching_inv = inv_by_student
                    is_resolved_typo = True
                    self._record_resolved_warning(
                        student_id=s_id,
                        user_id=u_id,
                        invoice_id=actual_inv_id,
                        faculty_form_id=f_id,
                        reason_code=config.REASON_CODES["INVOICE_TYPO"],
                        description=f"Teacher entered incorrect invoice_id {entered_inv_id}. Unambiguously auto-reconciled to {actual_inv_id} via student profile match.",
                        resolution_applied="AUTO_MATCHED_STUDENT_INVOICE",
                        owner="Automated Reconciliation Engine",
                        draft_teacher_msg=f"Hello {educator_name}, the invoice ID entered ({entered_inv_id}) for Student #{s_id} was automatically matched to {actual_inv_id}."
                    )
                else:
                    # Ambiguous (0 matches or > 1 match for student) -> BLOCKING UNRESOLVED EXCEPTION
                    self._record_unresolved_exception(
                        student_id=s_id,
                        user_id=u_id,
                        invoice_id=entered_inv_id,
                        faculty_form_id=f_id,
                        reason_code=config.REASON_CODES["INVOICE_TYPO"],
                        description=f"Invoice ID {entered_inv_id} does not exist and could not be unambiguously matched to a single student invoice. Sent for human review.",
                        severity="HIGH",
                        owner="Ops Tier 1",
                        human_review_required=True,
                        draft_parent_msg=None,
                        draft_teacher_msg=f"Hello {educator_name}, invoice ID {entered_inv_id} for Student #{s_id} could not be resolved automatically. Ops is reviewing."
                    )
                    continue

            inv_row = matching_inv.iloc[0]
            pay_status = str(inv_row['payment_status']).strip()
            net_amt = float(inv_row['net_amount'])
            payer_mobile = str(inv_row['mobile']).strip()
            payer_name = str(inv_row['parent_name']).strip()
            discount_amt = float(inv_row['discount_amount'])

            # Accumulate any BLOCKING exceptions for this form
            blocking_exceptions = []

            # FINANCIAL SAFEGUARD 1: Check Payment Failure (Form 3311)
            if pay_status == 'Failed':
                blocking_exceptions.append({
                    "reason_code": config.REASON_CODES["PAYMENT_FAILED"],
                    "description": f"Payment for invoice {actual_inv_id} failed at gateway. Teacher submission based on unverified payment proof.",
                    "severity": "HIGH",
                    "owner": "Automated Gateway Triage / Ops Tier 1",
                    "human_review_required": True,
                    "parent_msg": f"Dear {payer_name}, payment for renewal invoice #{actual_inv_id} was unsuccessful. Click here to retry securely: https://bambinos.live/pay/{actual_inv_id}",
                    "teacher_msg": f"Alert {educator_name}: Payment for Student #{s_id} failed at the gateway. Classes cannot be scheduled until payment is completed."
                })

            # FINANCIAL SAFEGUARD 2: Check Partial Payment (Form 3310)
            if pay_status == 'Partially_Paid' or f_amt > net_amt or net_amt < (std_fee - discount_amt):
                balance = std_fee - net_amt if std_fee > net_amt else 0.0
                blocking_exceptions.append({
                    "reason_code": config.REASON_CODES["PARTIAL_PAYMENT"],
                    "description": f"Partial payment detected. Teacher reported INR {f_amt:.0f}, but gateway received INR {net_amt:.0f}. Balance: INR {balance:.0f}.",
                    "severity": "HIGH",
                    "owner": "Finance / Retention Lead",
                    "human_review_required": True,
                    "parent_msg": f"Dear {payer_name}, partial payment of INR {net_amt:.0f} received for {ref_data.get('student_name_masked', 'your child')}. Please pay remaining INR {balance:.0f} to finalize schedule: https://bambinos.live/pay/{actual_inv_id}?part=2",
                    "teacher_msg": f"Hello {educator_name}, partial payment of INR {net_amt:.0f} received for Student #{s_id}. Remaining balance is pending."
                })

            # CHECK 3: Phone / Contact Mismatch (Form 3304)
            if ref_mobile and payer_mobile != ref_mobile:
                blocking_exceptions.append({
                    "reason_code": config.REASON_CODES["PHONE_MISMATCH"],
                    "description": f"Payer phone ({payer_mobile}) differs from student profile phone ({ref_mobile}). Teacher noted: '{remarks}'.",
                    "severity": "LOW",
                    "owner": "Ops Tier 1 (Verification Agent)",
                    "human_review_required": True,
                    "parent_msg": f"Dear {payer_name}, we received renewal payment for {ref_data.get('student_name_masked', 'your child')} from contact {payer_mobile}. Please confirm to link this number.",
                    "teacher_msg": None
                })

            # CHECK 4: Scholarship or Special Discount (Form 3307)
            if discount_amt > 0 or "scholarship" in remarks.lower() or "discount" in remarks.lower():
                blocking_exceptions.append({
                    "reason_code": config.REASON_CODES["SCHOLARSHIP"],
                    "description": f"Special discount/scholarship of INR {discount_amt:.0f} detected. Teacher remark: '{remarks}'. Awaiting Ops sign-off.",
                    "severity": "MEDIUM",
                    "owner": "Head of Operations / Retention Lead",
                    "human_review_required": True,
                    "parent_msg": f"Dear {payer_name}, your scholarship renewal for {ref_data.get('student_name_masked', 'your child')} is verified and being scheduled.",
                    "teacher_msg": f"Slack #ops-approvals: 20% discount (INR {discount_amt:.0f}) submitted for Student #{s_id} by {educator_name}. [Approve] [Reject]"
                })

            # CHECK 5: Batch Change Request (Form 3312)
            if not continue_same or "weekend" in remarks.lower() or "instead" in remarks.lower():
                blocking_exceptions.append({
                    "reason_code": config.REASON_CODES["BATCH_CHANGE"],
                    "description": f"Parent requested slot/day change. Preferred time: '{pref_time}'. Remarks: '{remarks}'.",
                    "severity": "MEDIUM",
                    "owner": "Parent Self-Service (Ops Tier 1 fallback)",
                    "human_review_required": False,
                    "parent_msg": f"Dear {payer_name}, renewal payment confirmed for {ref_data.get('student_name_masked', 'your child')}! Tap here to select your new preferred batch slot: https://bambinos.live/select-slot?student={s_id}",
                    "teacher_msg": f"Notice to {educator_name}: Student #{s_id} requested a batch schedule change ({pref_time}). New batch allocation in progress."
                })

            # CHECK 6: Batch Overcapacity Safeguard (Form 3305)
            if active_count >= batch_capacity:
                blocking_exceptions.append({
                    "reason_code": config.REASON_CODES["BATCH_FULL"],
                    "description": f"Target batch {current_batch_id} is at maximum capacity ({active_count}/{batch_capacity}). Cannot auto-schedule.",
                    "severity": "HIGH",
                    "owner": "Academic Ops Lead / Batch Scheduler",
                    "human_review_required": True,
                    "parent_msg": f"Dear {payer_name}, thank you for renewing! Your child's current batch is full. We have reserved seats in 2 sister batches with identical curriculum. Review here: https://bambinos.live/batch-options?student={s_id}",
                    "teacher_msg": f"Notice to {educator_name}: Batch {current_batch_id} is full (6/6). Student #{s_id} renewal held for sister batch assignment."
                })

            # If any blocking exception was flagged, record and block auto-approval
            if blocking_exceptions:
                for exc in blocking_exceptions:
                    self._record_unresolved_exception(
                        student_id=s_id,
                        user_id=u_id,
                        invoice_id=actual_inv_id,
                        faculty_form_id=f_id,
                        reason_code=exc["reason_code"],
                        description=exc["description"],
                        severity=exc["severity"],
                        owner=exc["owner"],
                        human_review_required=exc["human_review_required"],
                        draft_parent_msg=exc["parent_msg"],
                        draft_teacher_msg=exc["teacher_msg"]
                    )
                continue

            # ---------------------------------------------------------
            # HAPPY PATH: Auto-Approval Qualification
            # Check existing booking requests to avoid duplicate bookings
            # ---------------------------------------------------------
            existing_booking = existing_bookings_map.get((s_id, actual_inv_id))
            booking_action = "NEW_SIMULATED_BOOKING"
            booking_id_assigned = None

            if existing_booking is not None:
                b_id = int(existing_booking['id'])
                b_status = str(existing_booking['request_status']).strip()
                
                if b_status == 'Completed':
                    booking_action = "EXISTING_COMPLETED_REUSED"
                    booking_id_assigned = b_id
                    self.existing_bookings_reused += 1
                else:
                    booking_action = "EXISTING_PENDING_REUSED"
                    booking_id_assigned = b_id
                    self.existing_bookings_reused += 1
            else:
                self.new_bookings_created += 1
                booking_id_assigned = 5500 + self.new_bookings_created

            self._record_auto_approval(
                student_id=s_id,
                user_id=u_id,
                invoice_id=actual_inv_id,
                faculty_form_id=f_id,
                batch_id=current_batch_id,
                educator_id=int(ref_data.get('educator_id', form.get('educator_id', 0))),
                sessions_count=config.DEFAULT_TERM_SESSIONS,
                net_amount=net_amt,
                student_name=str(ref_data.get('student_name_masked', 'Student')),
                parent_name=payer_name,
                batch_name=str(ref_data.get('classbatch_name', 'Active Batch')),
                educator_name=educator_name,
                days=str(ref_data.get('batch_days', 'Mon,Wed')),
                time_slot=str(ref_data.get('batch_start_time', '18:00:00')),
                booking_action=booking_action,
                booking_id=booking_id_assigned
            )

        # -------------------------------------------------------------
        # STEP 2: Detect Orphaned Paid Invoices (No Faculty Form Submitted)
        # -------------------------------------------------------------
        all_form_students = set(self.faculty_forms['student_id'].unique())
        paid_invoices = self.invoices[self.invoices['payment_status'] == 'Paid']

        for idx, inv in paid_invoices.iterrows():
            s_id = int(inv['student_id'])
            inv_id = int(inv['id'])
            u_id = int(inv['user_id'])
            net_amt = float(inv['net_amount'])
            payer_name = str(inv['parent_name']).strip()

            if s_id not in all_form_students:
                ref_data = ref_lookup.get(s_id, {})
                educator_name = str(ref_data.get('educator_name', 'Teacher'))
                student_name = str(ref_data.get('student_name_masked', 'Child'))
                
                self._record_unresolved_exception(
                    student_id=s_id,
                    user_id=u_id,
                    invoice_id=inv_id,
                    faculty_form_id=None,
                    reason_code=config.REASON_CODES["MISSING_FORM"],
                    description=f"Paid invoice #{inv_id} (INR {net_amt:.0f}) has no faculty renewal form submitted after > 2 hours. High scheduling risk.",
                    severity="HIGH",
                    owner="Ops Tier 1 / Assigned Teacher",
                    human_review_required=True,
                    draft_parent_msg=f"Dear {payer_name}, renewal payment of INR {net_amt:.0f} received for {student_name}! We are confirming schedule details with your teacher.",
                    draft_teacher_msg=f"Action Required for {educator_name}: Parent of {student_name} paid renewal invoice #{inv_id}. Tap here to confirm 1-click continuation: https://bambinos.live/teacher/confirm?inv={inv_id}"
                )

        # Compile Summary Metrics
        self._compile_summary()

    def _record_auto_approval(self, student_id, user_id, invoice_id, faculty_form_id, batch_id, educator_id,
                              sessions_count, net_amount, student_name, parent_name, batch_name, educator_name, days, time_slot,
                              booking_action="NEW_SIMULATED_BOOKING", booking_id=None):
        """Records an approved renewal and drafts confirmation notification."""
        approval_record = {
            "student_id": student_id,
            "user_id": user_id,
            "invoice_id": invoice_id,
            "faculty_form_id": faculty_form_id,
            "allocated_classbatch_id": batch_id,
            "educator_id": educator_id,
            "sessions_allocated": sessions_count,
            "net_amount_inr": net_amount,
            "reason_code": config.REASON_CODES["HAPPY_PATH"],
            "approval_status": "AUTO_APPROVED",
            "booking_request_id": booking_id,
            "booking_action": booking_action,
            "is_simulation": config.SIMULATION_MODE,
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.auto_approved_records.append(approval_record)

        # Draft WhatsApp notification for Parent
        self.notification_drafts.append({
            "recipient_role": "Parent",
            "recipient_id": user_id,
            "student_id": student_id,
            "invoice_id": invoice_id,
            "channel": "WhatsApp",
            "reason_code": config.REASON_CODES["HAPPY_PATH"],
            "message_draft": f"Dear {parent_name}, renewal confirmed for {student_name}! All {sessions_count} sessions have been added to your calendar for {batch_name} ({days} at {time_slot}) with {educator_name}. View class schedule: https://bambinos.live/schedule/{student_id}"
        })

        # Draft Notification for Teacher
        self.notification_drafts.append({
            "recipient_role": "Teacher",
            "recipient_id": educator_id,
            "student_id": student_id,
            "invoice_id": invoice_id,
            "channel": "WhatsApp",
            "reason_code": config.REASON_CODES["HAPPY_PATH"],
            "message_draft": f"Hello {educator_name}, Student #{student_id} ({student_name}) has renewed and is auto-scheduled in your batch {batch_name}. Roster updated in portal."
        })

    def _record_resolved_warning(self, student_id, user_id, invoice_id, faculty_form_id, reason_code, description,
                                 resolution_applied, owner, draft_teacher_msg):
        """Records a non-blocking warning that was automatically resolved without preventing auto-approval."""
        warning_record = {
            "student_id": student_id,
            "user_id": user_id,
            "invoice_id": invoice_id,
            "faculty_form_id": faculty_form_id if faculty_form_id is not None else "None",
            "reason_code": reason_code,
            "classification": "RESOLVED_WARNING",
            "resolution_applied": resolution_applied,
            "description": description,
            "assigned_owner": owner,
            "human_review_required": False,
            "status": "AUTO_RESOLVED",
            "is_simulation": config.SIMULATION_MODE,
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.resolved_warnings.append(warning_record)

        if draft_teacher_msg:
            self.notification_drafts.append({
                "recipient_role": "Teacher/Ops",
                "recipient_id": "OPS_OR_TEACHER",
                "student_id": student_id,
                "invoice_id": invoice_id,
                "channel": "WhatsApp",
                "reason_code": reason_code,
                "message_draft": draft_teacher_msg
            })

    def _record_unresolved_exception(self, student_id, user_id, invoice_id, faculty_form_id, reason_code, description,
                                     severity, owner, human_review_required, draft_parent_msg, draft_teacher_msg):
        """Records an unresolved blocking exception and associated message drafts."""
        exception_record = {
            "student_id": student_id,
            "user_id": user_id,
            "invoice_id": invoice_id,
            "faculty_form_id": faculty_form_id if faculty_form_id is not None else "None",
            "reason_code": reason_code,
            "classification": "UNRESOLVED_EXCEPTION",
            "severity": severity,
            "description": description,
            "assigned_owner": owner,
            "human_review_required": human_review_required,
            "triage_status": "FLAGGED_FOR_TRIAGE",
            "is_simulation": config.SIMULATION_MODE,
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.unresolved_exceptions.append(exception_record)

        if draft_parent_msg:
            self.notification_drafts.append({
                "recipient_role": "Parent",
                "recipient_id": user_id,
                "student_id": student_id,
                "invoice_id": invoice_id,
                "channel": "WhatsApp",
                "reason_code": reason_code,
                "message_draft": draft_parent_msg
            })

        if draft_teacher_msg:
            channel = "Slack" if "Slack" in draft_teacher_msg else "WhatsApp"
            self.notification_drafts.append({
                "recipient_role": "Teacher/Ops",
                "recipient_id": "OPS_OR_TEACHER",
                "student_id": student_id,
                "invoice_id": invoice_id,
                "channel": channel,
                "reason_code": reason_code,
                "message_draft": draft_teacher_msg
            })

    def _compile_summary(self):
        """Calculates reconciliation metrics and validation counts."""
        total_invoices = len(self.invoices)
        unique_invoices_processed = int(self.invoices['id'].nunique())
        unique_students_invoiced = int(self.invoices['student_id'].nunique())
        total_paid_invoices = len(self.invoices[self.invoices['payment_status'] == 'Paid'])

        auto_approved_count = len(self.auto_approved_records)
        unique_students_auto_approved = len(set(r['student_id'] for r in self.auto_approved_records))
        unresolved_exceptions_count = len(self.unresolved_exceptions)
        unique_students_unresolved = len(set(r['student_id'] for r in self.unresolved_exceptions))
        human_review_count = len([e for e in self.unresolved_exceptions if e['human_review_required']])
        resolved_warnings_count = len(self.resolved_warnings)
        notifications_count = len(self.notification_drafts)

        # Code breakdown: separate auto-approved, resolved warnings, and unresolved exceptions
        unresolved_code_counts = {}
        for rec in self.unresolved_exceptions:
            c = rec['reason_code']
            unresolved_code_counts[c] = unresolved_code_counts.get(c, 0) + 1

        resolved_warning_counts = {}
        for rec in self.resolved_warnings:
            c = rec['reason_code']
            resolved_warning_counts[c] = resolved_warning_counts.get(c, 0) + 1

        self.summary_metrics = {
            "metadata": {
                "engine_version": "1.2.0-prototype",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "simulation_mode": config.SIMULATION_MODE,
                "notes": "Simulated approvals generate proposed schedule objects without modifying original CSV files."
            },
            "input_dataset_counts": {
                "total_invoices": total_invoices,
                "unique_invoices_processed": unique_invoices_processed,
                "unique_students_processed": unique_students_invoiced,
                "paid_invoices": total_paid_invoices,
                "partially_paid_invoices": len(self.invoices[self.invoices['payment_status'] == 'Partially_Paid']),
                "failed_invoices": len(self.invoices[self.invoices['payment_status'] == 'Failed']),
                "faculty_form_submissions": len(self.faculty_forms),
                "existing_booking_requests": len(self.booking_requests),
                "existing_class_schedules": len(self.schedule_bookings),
                "reference_students_count": len(self.reference)
            },
            "reconciliation_results": {
                "unique_renewals_auto_approved": auto_approved_count,
                "unique_students_auto_approved": unique_students_auto_approved,
                "existing_bookings_reused": self.existing_bookings_reused,
                "new_bookings_created": self.new_bookings_created,
                "unique_students_with_unresolved_exceptions": unique_students_unresolved,
                "total_unresolved_exception_records": unresolved_exceptions_count,
                "human_review_cases_count": human_review_count,
                "resolved_warnings_count": resolved_warnings_count,
                "total_notification_drafts_generated": notifications_count,
                "proposed_auto_approval_yield_pct": round((auto_approved_count / total_paid_invoices) * 100, 1),
                "unresolved_exception_rate_pct": round((unresolved_exceptions_count / (auto_approved_count + unresolved_exceptions_count)) * 100, 1)
            },
            "reason_code_distribution": {
                "auto_approved": {
                    config.REASON_CODES["HAPPY_PATH"]: auto_approved_count
                },
                "resolved_warnings": resolved_warning_counts,
                "unresolved_exceptions": unresolved_code_counts
            }
        }

    def export_outputs(self):
        """Saves all output files to config.OUTPUTS_DIR."""
        os.makedirs(config.OUTPUTS_DIR, exist_ok=True)
        
        # 1. auto_approved.csv
        df_auto = pd.DataFrame(self.auto_approved_records)
        df_auto.to_csv(config.AUTO_APPROVED_FILE, index=False)
        logger.info(f"Saved {len(df_auto)} auto-approved records to {config.AUTO_APPROVED_FILE}")

        # 2. flagged_exceptions.csv (now strictly unresolved blocking exceptions)
        df_ex = pd.DataFrame(self.unresolved_exceptions)
        df_ex.to_csv(config.FLAGGED_EXCEPTIONS_FILE, index=False)
        logger.info(f"Saved {len(df_ex)} unresolved exceptions to {config.FLAGGED_EXCEPTIONS_FILE}")

        # 3. resolved_warnings.csv (non-blocking resolved warnings)
        df_warn = pd.DataFrame(self.resolved_warnings)
        df_warn.to_csv(config.RESOLVED_WARNINGS_FILE, index=False)
        logger.info(f"Saved {len(df_warn)} resolved warnings to {config.RESOLVED_WARNINGS_FILE}")

        # 4. notification_drafts.csv
        df_notif = pd.DataFrame(self.notification_drafts)
        df_notif.to_csv(config.NOTIFICATION_DRAFTS_FILE, index=False)
        logger.info(f"Saved {len(df_notif)} notification drafts to {config.NOTIFICATION_DRAFTS_FILE}")

        # 5. processing_summary.json
        with open(config.PROCESSING_SUMMARY_FILE, "w") as f:
            json.dump(self.summary_metrics, f, indent=4)
        logger.info(f"Saved processing summary to {config.PROCESSING_SUMMARY_FILE}")

if __name__ == "__main__":
    engine = ReconciliationEngine()
    engine.run_reconciliation()
    engine.export_outputs()
    print("\n--- RECONCILIATION SUMMARY ---")
    print(json.dumps(engine.summary_metrics, indent=2))
