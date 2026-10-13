import copy
import os
import unittest
from tools.p09 import qualify_native_owned_exit_wait_environment as a
from tools.p09 import run_native_owned_exit_wait_environment_batch as dispatch
class OwnedExitEnvironmentTests(unittest.TestCase):
    def test_child_environment_changes_only_legacy_module_path_not_parent_or_policy(self):
        parent={"PSModulePath":"non_native_parent_path","P09_TEST_SENTINEL":"preserved"};before=dict(parent)
        child=a.child_environment(parent)
        self.assertEqual(parent,before);self.assertEqual(child["P09_TEST_SENTINEL"],"preserved")
        self.assertEqual(child["PSModulePath"],";".join(a.LEGACY_PATHS));self.assertEqual(set(child),set(parent))
        real=dict(os.environ);a.child_environment();self.assertEqual(dict(os.environ),real)
    def test_whole_dispatcher_inverse_only_fixed_import_and_child_environment_changed(self):
        self.assertTrue(a.dispatcher_inverse())
        self.assertEqual(len(a.own_pins()),6)
        raw=a.public.bounded_bytes(a.ROOT/"tools/p09/run_native_owned_exit_wait_environment_batch.py",65536)
        self.assertNotIn(b"ExecutionPolicy",raw);self.assertNotIn(b"Stop-Process",raw);self.assertNotIn(b"taskkill",raw)
        self.assertEqual(raw.count(b"env=a.child_environment()"),2)
    def test_prefix_probe_is_exact_original_pre_native_body_no_com_or_run_creation(self):
        self.assertTrue(a.prefix_inverse())
        source=a.public.bounded_bytes(a.ROOT/a.PROBE,65536)
        self.assertNotIn(b"[void][IO.Directory]::CreateDirectory($run)",source)
        self.assertNotIn(b"$session = New-ExactHwpSession",source)
    def test_old_r04_first_case_has_no_trace_or_owned_session_to_promote(self):
        self.assertFalse(any(path.exists() for path in a.binding.attempt_paths(a.previous.PREFIX)))
        raw=a.public.checked(a.ROOT/a.previous.CAPSULE,a.PREVIOUS_SHA,2097152)
        import json
        old=json.loads(raw);self.assertFalse(old["claims"]["actual_owned_exit_wait_native_tested"])
        self.assertFalse((a.ROOT/a.previous.DISPATCH).exists())
    def test_new_fixed_capsule_paths_reject_prior_private_alias_and_traversal(self):
        self.assertEqual(a.path_guard(a.ROOT/a.CAPSULE),a.ROOT/a.CAPSULE)
        for path in (a.ROOT/a.previous.CAPSULE,a.ROOT/a.prior.CAPSULE,a.ROOT/"implementation/p09/evidence/private/x.json",
                     a.ROOT/"implementation/p09/evidence/P09-36-native-form-owned-exit-environment.r05.json",
                     a.ROOT/"implementation/p09/evidence/../evidence/p09-36-native-form-owned-exit-environment.r05.json"):
            with self.assertRaises(ValueError):a.path_guard(path)
    def test_full_new_fifteen_case_inventory_and_zero_threshold_remain_strict(self):
        manifest=a.q.shared.lifecycle.checked_json(a.ROOT/a.binding.MANIFEST,a.binding.MANIFEST_SHA)
        if any(path.exists() for path in a.binding.attempt_paths(a.PREFIX)):
            with self.assertRaisesRegex(ValueError,"owned_exit_dispatch_attempt_exists"):dispatch.case_plan(manifest)
        else:self.assertEqual(len(dispatch.case_plan(manifest)),15)
        for rows in (manifest["cases"][:2],manifest["cases"]+manifest["cases"][:1]):
            with self.assertRaises(ValueError):dispatch.case_plan({**manifest,"cases":rows})
        with self.assertRaises(ValueError):dispatch.case_plan(manifest,a.previous.PREFIX)
        original=a.public.checked(a.ROOT/a.HARNESS,a.HARNESS_SHA)
        self.assertIn(b"remaining_hwp_process_count -ne 0) { exit 2 }",original)
if __name__=="__main__":unittest.main()
