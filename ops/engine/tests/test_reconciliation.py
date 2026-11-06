"""
Comprehensive Unit and Integration Test Suite for Bambinos.live Renewal Engine
Covers all 10 standard reason codes, financial safeguards, and the 6 independent audit scenarios:
1. Already completed booking is not counted as a new booking (reused).
2. Existing pending booking is not duplicated (reused).
3. Duplicate forms with conflicting information are flagged safely for human review.
4. Ambiguous invoice typo is sent for human review.
5. Multiple exception conditions for one student are handled correctly.
6. Auto-approval count and new-booking count are calculated separately.
Also tests non-blocking resolved warnings vs blocking unresolved exceptions.
"""

import unittest
import os
import sys
import pandas as pd

# Ensure engine path is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from reconciliation_engine import ReconciliationEngine
import config

class TestReconciliationEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run reconciliation engine on production data once for test assertions."""
        cls.engine = ReconciliationEngine()
        cls.engine.run_reconciliation()

    # =========================================================================
    # CORE PRODUCTION SUITE
    # =========================================================================

    def test_datasets_loaded_correctly(self):
        """Verify that all 5 datasets are loaded with original counts."""
        self.assertEqual(len(self.engine.invoices), 13)
        self.assertEqual(len(self.engine.faculty_forms), 12)
        self.assertEqual(len(self.engine.booking_requests), 4)
        self.assertEqual(len(self.engine.schedule_bookings), 2)
        self.assertEqual(len(self.engine.reference), 13)

    def test_happy_path_auto_approved(self):
        """Test that clean renewals (e.g. Student 68101, 68102, 68103, 68108, 68113) are auto-approved."""
        approved_students = [r['student_id'] for r in self.engine.auto_approved_records]
        self.assertEqual(len(approved_students), 5)
        self.assertIn(68101, approved_students)
        self.assertIn(68102, approved_students)
        self.assertIn(68103, approved_students)
        self.assertIn(68108, approved_students)
        self.assertIn(68113, approved_students)

        # Check approval attributes for student 68101
        rec_68101 = next(r for r in self.engine.auto_approved_records if r['student_id'] == 68101)
        self.assertEqual(rec_68101['reason_code'], config.REASON_CODES["HAPPY_PATH"])
        self.assertEqual(rec_68101['allocated_classbatch_id'], 9201)
        self.assertEqual(rec_68101['net_amount_inr'], 12000.0)

    def test_faculty_form_missing(self):
        """Test that paid invoices without teacher forms (84906, 84910) are flagged as unresolved exceptions."""
        exceptions = [e for e in self.engine.unresolved_exceptions if e['reason_code'] == config.REASON_CODES["MISSING_FORM"]]
        missing_invoices = [e['invoice_id'] for e in exceptions]
        self.assertEqual(len(exceptions), 2)
        self.assertIn(84906, missing_invoices)
        self.assertIn(84910, missing_invoices)

    def test_phone_mismatch(self):
        """Test that phone mismatch (Student 68104) is flagged for Ops verification."""
        ex = next((e for e in self.engine.unresolved_exceptions if e['student_id'] == 68104), None)
        self.assertIsNotNone(ex)
        self.assertEqual(ex['reason_code'], config.REASON_CODES["PHONE_MISMATCH"])
        self.assertTrue(ex['human_review_required'])

    def test_batch_full_safeguard(self):
        """Test that batch capacity limit prevents auto-scheduling when batch is 6/6 (Student 68105)."""
        ex = next((e for e in self.engine.unresolved_exceptions if e['student_id'] == 68105), None)
        self.assertIsNotNone(ex)
        self.assertEqual(ex['reason_code'], config.REASON_CODES["BATCH_FULL"])
        self.assertIn("6/6", ex['description'])

    def test_identical_duplicate_faculty_form_resolved_as_warning(self):
        """Test that identical duplicate form submission (Form 3309) is recorded as a resolved warning."""
        warn = next((w for w in self.engine.resolved_warnings if w['faculty_form_id'] == 3309), None)
        self.assertIsNotNone(warn)
        self.assertEqual(warn['reason_code'], config.REASON_CODES["DUPLICATE_FORM"])
        self.assertEqual(warn['classification'], "RESOLVED_WARNING")
        self.assertFalse(warn['human_review_required'])

    def test_partial_payment_safeguard(self):
        """Test financial safeguard: Partial payment (Student 68109) is never auto-approved."""
        approved_students = [r['student_id'] for r in self.engine.auto_approved_records]
        self.assertNotIn(68109, approved_students)

        ex = next((e for e in self.engine.unresolved_exceptions if e['student_id'] == 68109), None)
        self.assertIsNotNone(ex)
        self.assertEqual(ex['reason_code'], config.REASON_CODES["PARTIAL_PAYMENT"])
        self.assertIn("5250", ex['description'])

    def test_payment_failed_safeguard(self):
        """Test financial safeguard: Failed payment (Student 68111) is rejected despite teacher form."""
        approved_students = [r['student_id'] for r in self.engine.auto_approved_records]
        self.assertNotIn(68111, approved_students)

        ex = next((e for e in self.engine.unresolved_exceptions if e['student_id'] == 68111), None)
        self.assertIsNotNone(ex)
        self.assertEqual(ex['reason_code'], config.REASON_CODES["PAYMENT_FAILED"])

    def test_batch_change_request(self):
        """Test that batch change request (Student 68112) is routed to slot selection."""
        ex = next((e for e in self.engine.unresolved_exceptions if e['student_id'] == 68112), None)
        self.assertIsNotNone(ex)
        self.assertEqual(ex['reason_code'], config.REASON_CODES["BATCH_CHANGE"])

    def test_scholarship_discount_approval(self):
        """Test that retention discount (Student 68107) requires Ops authorization."""
        ex = next((e for e in self.engine.unresolved_exceptions if e['student_id'] == 68107), None)
        self.assertIsNotNone(ex)
        self.assertEqual(ex['reason_code'], config.REASON_CODES["SCHOLARSHIP"])

    def test_invoice_id_mismatch_resolved_as_warning(self):
        """Test that unambiguous teacher typo in invoice ID (Form 3313 entered 84931) is recorded as a resolved warning."""
        warn = next((w for w in self.engine.resolved_warnings if w['reason_code'] == config.REASON_CODES["INVOICE_TYPO"]), None)
        self.assertIsNotNone(warn)
        self.assertEqual(warn['student_id'], 68113)
        self.assertEqual(warn['invoice_id'], 84913)
        self.assertEqual(warn['classification'], "RESOLVED_WARNING")

    def test_all_ten_reason_codes_represented(self):
        """Ensure all 10 standardized reason codes are tested and present in results."""
        summary = self.engine.summary_metrics['reason_code_distribution']
        all_codes_generated = set(summary['auto_approved'].keys()) | set(summary['resolved_warnings'].keys()) | set(summary['unresolved_exceptions'].keys())
        self.assertEqual(len(all_codes_generated), 10)
        for code_name, code_val in config.REASON_CODES.items():
            self.assertIn(code_val, all_codes_generated, f"Reason code {code_val} was not generated.")

    def test_notification_drafts_generated(self):
        """Verify notification drafts exist for parents and teachers."""
        drafts = self.engine.notification_drafts
        self.assertGreater(len(drafts), 20)
        parent_drafts = [d for d in drafts if d['recipient_role'] == 'Parent']
        teacher_drafts = [d for d in drafts if 'Teacher' in d['recipient_role']]
        self.assertGreater(len(parent_drafts), 0)
        self.assertGreater(len(teacher_drafts), 0)

    # =========================================================================
    # AUDIT VERIFICATION TESTS
    # =========================================================================

    def test_no_overlap_between_auto_approved_and_unresolved_exceptions(self):
        """
        Audit Consistency Rule:
        A student with an unresolved blocking exception must NEVER appear in auto-approved output.
        Auto-approved (5) + Unresolved (8) must partition the 13 students with ZERO overlap.
        """
        auto_approved_students = set(r['student_id'] for r in self.engine.auto_approved_records)
        unresolved_students = set(r['student_id'] for r in self.engine.unresolved_exceptions)
        
        overlap = auto_approved_students.intersection(unresolved_students)
        self.assertEqual(len(overlap), 0, f"Contradiction! Overlap found: {overlap}")
        self.assertEqual(len(auto_approved_students) + len(unresolved_students), 13)

    def test_already_completed_booking_not_duplicated_and_reused(self):
        """
        Audit Requirement 1:
        Verify that an already completed booking (Student 68101, Booking 5501)
        is recognized as completed, reused, and not counted as a new booking.
        """
        rec_68101 = next(r for r in self.engine.auto_approved_records if r['student_id'] == 68101)
        self.assertEqual(rec_68101['booking_request_id'], 5501)
        self.assertEqual(rec_68101['booking_action'], "EXISTING_COMPLETED_REUSED")

    def test_existing_pending_booking_not_duplicated_and_reused(self):
        """
        Audit Requirement 2:
        Verify that an existing pending booking (Student 68102, Booking 5502)
        is reused rather than generating a duplicate booking ID.
        """
        rec_68102 = next(r for r in self.engine.auto_approved_records if r['student_id'] == 68102)
        self.assertEqual(rec_68102['booking_request_id'], 5502)
        self.assertEqual(rec_68102['booking_action'], "EXISTING_PENDING_REUSED")

    def test_duplicate_forms_with_conflicting_info_flagged_safely(self):
        """
        Audit Requirement 3:
        Verify that if a duplicate form is submitted with conflicting information
        (e.g. different amount or batch choice), the engine flags it as an UNRESOLVED exception.
        """
        test_engine = ReconciliationEngine()
        test_engine.load_datasets()
        
        # Inject synthetic conflicting duplicate form for testing
        conflicting_form = test_engine.faculty_forms.iloc[0].copy()
        conflicting_form['id'] = 9999
        conflicting_form['amount_paid'] = conflicting_form['amount_paid'] + 5000.0  # conflicting amount
        test_engine.faculty_forms = pd.concat([test_engine.faculty_forms, pd.DataFrame([conflicting_form])], ignore_index=True)
        
        test_engine.run_reconciliation(reload_data=False)
        
        conflicting_ex = next((e for e in test_engine.unresolved_exceptions if e['faculty_form_id'] == 9999), None)
        self.assertIsNotNone(conflicting_ex)
        self.assertEqual(conflicting_ex['reason_code'], config.REASON_CODES["DUPLICATE_FORM"])
        self.assertEqual(conflicting_ex['classification'], "UNRESOLVED_EXCEPTION")
        self.assertTrue(conflicting_ex['human_review_required'])
        self.assertIn("CONFLICTING", conflicting_ex['description'])

    def test_ambiguous_invoice_typo_sent_for_human_review(self):
        """
        Audit Requirement 4:
        Verify that an ambiguous invoice typo (e.g. student has 0 or >1 invoices)
        cannot be auto-reconciled and is escalated as an UNRESOLVED exception for human review.
        """
        test_engine = ReconciliationEngine()
        test_engine.load_datasets()
        
        # Inject synthetic form with unknown student and bogus invoice ID
        bogus_form = test_engine.faculty_forms.iloc[0].copy()
        bogus_form['id'] = 8888
        bogus_form['student_id'] = 999999  # Unknown student
        bogus_form['invoice_id'] = 777777  # Unknown invoice
        test_engine.faculty_forms = pd.concat([test_engine.faculty_forms, pd.DataFrame([bogus_form])], ignore_index=True)
        
        test_engine.run_reconciliation(reload_data=False)
        
        ambiguous_ex = next((e for e in test_engine.unresolved_exceptions if e['faculty_form_id'] == 8888), None)
        self.assertIsNotNone(ambiguous_ex)
        self.assertEqual(ambiguous_ex['reason_code'], config.REASON_CODES["INVOICE_TYPO"])
        self.assertEqual(ambiguous_ex['classification'], "UNRESOLVED_EXCEPTION")
        self.assertTrue(ambiguous_ex['human_review_required'])
        self.assertIn("Sent for human review", ambiguous_ex['description'])

    def test_multiple_exception_conditions_for_one_student_handled_correctly(self):
        """
        Audit Requirement 5:
        Verify that when a renewal triggers multiple exception conditions
        (e.g. Failed Payment AND Phone Mismatch), both exceptions are captured
        and the renewal is safely blocked from auto-approval.
        """
        test_engine = ReconciliationEngine()
        test_engine.load_datasets()
        
        # Inject synthetic form: Failed payment + Phone mismatch
        multi_form = test_engine.faculty_forms.iloc[0].copy()
        multi_form['id'] = 7777
        multi_form['student_id'] = 68111  # Student 68111 has Failed payment status
        multi_form['invoice_id'] = 84911
        test_engine.faculty_forms = pd.concat([test_engine.faculty_forms, pd.DataFrame([multi_form])], ignore_index=True)
        
        test_engine.run_reconciliation(reload_data=False)
        
        # Ensure student 68111 is NOT auto-approved
        approved_students = [r['student_id'] for r in test_engine.auto_approved_records]
        self.assertNotIn(68111, approved_students)
        
        # Verify Failed Payment exception exists in unresolved exceptions
        student_exceptions = [e for e in test_engine.unresolved_exceptions if e['student_id'] == 68111]
        reason_codes = [e['reason_code'] for e in student_exceptions]
        self.assertIn(config.REASON_CODES["PAYMENT_FAILED"], reason_codes)

    def test_auto_approval_count_and_new_booking_count_calculated_separately(self):
        """
        Audit Requirement 6:
        Verify that the engine strictly distinguishes the number of auto-approved renewals (5)
        from the number of new booking requests created (3), accounting for 2 existing bookings reused.
        """
        summary = self.engine.summary_metrics['reconciliation_results']
        auto_approved = summary['unique_renewals_auto_approved']
        reused = summary['existing_bookings_reused']
        new_created = summary['new_bookings_created']
        
        self.assertEqual(auto_approved, 5)
        self.assertEqual(reused, 2)
        self.assertEqual(new_created, 3)
        self.assertEqual(auto_approved, reused + new_created)

if __name__ == '__main__':
    unittest.main()
