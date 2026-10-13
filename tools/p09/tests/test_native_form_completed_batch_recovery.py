import copy
import unittest
from tools.p09 import qualify_native_form_completed_batch_recovery as a

class CompletedBatchRecoveryTests(unittest.TestCase):
    def test_frozen_r05_sources_and_actual_missing_top_level_key_are_preserved(self):
        raw,value=a.frozen_admission()
        self.assertEqual(len(raw),32899)
        self.assertEqual(len(value["source_sha256"]),6)
        failure=a.dispatch_failure(value)
        self.assertEqual(failure["actual_missing_key_exception"],"KeyError")
        self.assertFalse(failure["original_dispatch_success_claimed"])
        self.assertFalse(failure["original_dispatch_receipt_published"])
        self.assertTrue(failure["correct_nested_prior_batch_is_byte_preserved"])
        changed=copy.deepcopy(value);changed["prior_partial_batch_preserved"]=value["prior_r04_admission"]["prior_partial_batch_preserved"]
        with self.assertRaisesRegex(ValueError,"completed_recovery_original_schema_failure_missing"):a.dispatch_failure(changed)

    def test_all_fifteen_actual_traces_seventy_five_files_and_thirty_sessions_are_bound(self):
        manifest,records,pins,inventory=a.actual_traces()
        self.assertEqual(len(manifest["cases"]),15);self.assertEqual(len(records),15);self.assertEqual(len(pins),75)
        self.assertEqual(inventory["owned_session_count"],30)
        self.assertEqual(inventory["passed_lifecycle_cases"],15)
        self.assertTrue(inventory["all_cases_sequential"] and inventory["all_owned_process_ids_unique"])
        self.assertEqual([record[0]["case_id"] for record in records],[f"P09-35-C{i:02}" for i in range(1,16)])
        self.assertTrue(all(record[2]["remaining_hwp_process_count"]==0 for record in records))

    def test_original_trace_binder_rejects_changed_input_identity_without_editing_files(self):
        _,records,_,_=a.actual_traces()
        row,path,trace,passed=records[0]
        changed=copy.deepcopy(row);changed["package_sha256"]="0"*64
        with self.assertRaises(ValueError):a.binding.verify_case_trace(trace,changed)
        wrong=copy.deepcopy(trace);wrong["remaining_hwp_process_count"]=1
        with self.assertRaises(ValueError):a.binding.verify_case_trace(wrong,row)
        self.assertTrue(a.binding.verify_case_trace(trace,row))

    def test_actual_public_reader_protocol_retains_failure_and_rejects_forged_digests(self):
        _,records,_,_=a.actual_traces();value=a.binding.rust_observations(a.admission.PREFIX)
        a.binding.verify_rust(value,records)
        self.assertEqual(len(value["cases"]),15)
        self.assertEqual(value["green_rows"],0)
        changed=copy.deepcopy(value);changed["cases"][0]["saved"]["package_sha256"]="0"*64
        with self.assertRaises(ValueError):a.binding.verify_rust(changed,records)
        with self.assertRaises(ValueError):a.binding.verify_rust({**value,"cases":value["cases"][:-1]},records)

    def test_new_fixed_output_rejects_original_dispatch_bound_private_and_traversal(self):
        self.assertEqual(a.path_guard(a.ROOT/a.CAPSULE),a.ROOT/a.CAPSULE)
        for path in (a.ROOT/a.admission.CAPSULE,a.ROOT/a.admission.DISPATCH,a.ROOT/a.admission.BOUND,
                     a.ROOT/"implementation/p09/evidence/private/recovery.json",
                     a.ROOT/"implementation/p09/evidence/../evidence/p09-36-native-form-complete-recovery.r06.json"):
            with self.assertRaises(ValueError):a.path_guard(path)
        self.assertEqual(len(a.own_pins()),6)

    def test_raw_equality_rejects_nonbytes_extra_missing_and_changed_bytes(self):
        a.prior.raw_equal(b"{}",b"{}")
        for left,right in (("{}",b"{}"),(b"{}","{}"),(b"{}{}",b"{}"),(b"",b"{}"),(b"{ }",b"{}")):
            with self.assertRaises(ValueError):a.prior.raw_equal(left,right)

if __name__=="__main__":unittest.main()
