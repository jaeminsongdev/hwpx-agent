import copy
import json
import unittest
from tools.p09 import qualify_native_owned_exit_wait_admission as a
from tools.p09 import run_native_owned_exit_wait_batch as dispatch
class OwnedExitAdmissionTests(unittest.TestCase):
    def test_complete_candidate_inverse_and_same_zero_exit_reject_unrelated_change(self):
        original=a.public.checked(a.ROOT/a.q.HARNESS,a.q.HARNESS_SHA)
        current=a.public.checked(a.ROOT/a.HARNESS,a.HARNESS_SHA)
        a.inverse(current,original)
        for bad in (current+b"\n",current.replace(a.WAIT,b"",1),current.replace(a.WAIT,a.WAIT+a.WAIT,1),
                    current.replace(b"remaining_hwp_process_count -ne 0) { exit 2 }",b"remaining_hwp_process_count -ne 0) { exit 0 }")):
            with self.assertRaises(ValueError):a.inverse(bad,original)
    def test_exact_raw_byte_protocol_rejects_types_missing_extra_and_mutation(self):
        a.prior.raw_equal(b"{}",b"{}")
        for bad in (b"",b"{}\n",b"{}{}","{}",None,{},bytearray(b"{}")):
            with self.assertRaises(ValueError):a.prior.raw_equal(bad,b"{}")
    def test_old_seven_attempts_preserve_rejected_cleanup_and_all_thirty_five_files(self):
        value=a.prior_attempts();self.assertEqual(len(value["source_sha256"]),35)
        self.assertEqual(len(value["cases"]),7);self.assertEqual(value["not_run_cases"],8)
        self.assertEqual(value["cases"][-1]["recorded_remaining"],1)
        self.assertEqual(value["cases"][-1]["trace_binding"],"fail")
        self.assertFalse(value["old_failed_trace_edited_or_promoted"])
    def test_fixed_current_paths_reject_original_private_traversal_and_alias(self):
        self.assertEqual(a.path_guard(a.ROOT/a.CAPSULE),a.ROOT/a.CAPSULE)
        for path in (a.ROOT/a.prior.CAPSULE,a.ROOT/a.old.CAPSULE,a.ROOT/"implementation/p09/evidence/private/x.json",
                     a.ROOT/"implementation/p09/evidence/P09-36-native-form-owned-exit-admission.r04.json",
                     a.ROOT/"implementation/p09/evidence/../evidence/p09-36-native-form-owned-exit-admission.r04.json"):
            with self.assertRaises(ValueError):a.path_guard(path)
        self.assertEqual(len(a.own_pins()),8)
    def test_current_dispatch_inventory_only_complete_fifteen_cases_unique_unused_paths(self):
        manifest=a.q.shared.lifecycle.checked_json(a.ROOT/a.binding.MANIFEST,a.binding.MANIFEST_SHA)
        if any(path.exists() for path in a.binding.attempt_paths(a.PREFIX)):
            with self.assertRaisesRegex(ValueError,"owned_exit_dispatch_attempt_exists"):dispatch.case_plan(manifest)
        else:self.assertEqual(len(dispatch.case_plan(manifest)),15)
        for bad in (manifest["cases"],{**manifest,"cases":manifest["cases"][:2]},
                    {**manifest,"cases":manifest["cases"]+manifest["cases"][:1]}):
            with self.assertRaises(ValueError):dispatch.case_plan(bad)
        changed=copy.deepcopy(manifest);changed["cases"][0]["file"]="../outside.hwpx"
        with self.assertRaises(ValueError):dispatch.case_plan(changed)
        with self.assertRaises(ValueError):dispatch.case_plan(manifest,"p09-35-20261003-r03")
    def test_guard_protocol_requires_all_names_code_zero_no_skip_extra_or_coercion(self):
        module="tools.p09.tests.test_native_owned_exit_wait_admission";klass="OwnedExitAdmissionTests"
        text="\n".join(f"{name} ({module}.{klass}.{name}) ... ok" for name in sorted(a.GUARDS))+"\n\nRan 6 tests in 0.10s\n\nOK\n"
        self.assertEqual(a.guard_protocol(0,b"",text.encode(),module,klass,a.GUARDS)["passed"],6)
        for bad in (text.replace(" ... ok"," ... skipped",1),text+"extra",text.replace("Ran 6","Ran 5"),text.replace(" ... ok"," ... ERROR",1)):
            with self.assertRaises(ValueError):a.guard_protocol(0,b"",bad.encode(),module,klass,a.GUARDS)
        with self.assertRaises(ValueError):a.guard_protocol(1,b"",text.encode(),module,klass,a.GUARDS)
        with self.assertRaises(ValueError):a.guard_protocol(False,b"",text.encode(),module,klass,a.GUARDS)
        with self.assertRaises(ValueError):a.guard_protocol(0,b"extra",text.encode(),module,klass,a.GUARDS)
if __name__=="__main__":unittest.main()
