import sys
import io
import re
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_case112_current_library as check


class CheckRecipeTests(unittest.TestCase):
    def test_current_check_does_not_run_tests_or_replace_original_target(self):
        self.assertEqual(check.ARGS, ["check", "--quiet", "-p", "hwpx-agent-cli", "--lib"])
        self.assertNotIn("test", check.ARGS)
        self.assertNotEqual(check.target_for(1), check.owned.TARGET)
        self.assertEqual(check.target_for(1).parent, check.owned.ROOT / "target")
    def test_generations_and_worker_are_closed(self):
        for value in (0, 1000, True, "1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                check.task_for(value)
        self.assertNotEqual(check.target_for(1), check.target_for(2))
        with self.assertRaises(ValueError):check.worker("arbitrary-tests")
    def test_original_job_policy_is_one_cpu_one_cargo_and_percentage_ram(self):
        policy=check.owned.POLICY
        self.assertEqual(policy["logical_cpu_limit"],1)
        self.assertEqual(policy["cargo_jobs"],1)
        self.assertEqual(policy["emergency_cpu_percent"],98)
        self.assertEqual(policy["emergency_cpu_consecutive_samples"],4)
        self.assertEqual(policy["stop_ram_min_percent"],8)
        self.assertIn("job_memory_limit_percent",policy)
    def test_worker_keeps_original_token_and_job_owner_checks(self):
        seen=[]
        with patch.object(check.owned,"worker",side_effect=lambda task:seen.append(task) or 0):
            result=check.worker(check.task_for(991))
        self.assertEqual(result,0);self.assertEqual(seen,[check.task_for(991)])
    def test_closed_error_is_retained_by_original_driver(self):
        with self.assertRaises(ValueError) as raised:check.require(False,"SOURCE_DRIFT")
        self.assertIsNotNone(re.fullmatch(r"[A-Z_]+",str(raised.exception)))
    def test_completion_is_exact_and_does_not_filter_diagnostics(self):
        self.assertTrue(check.quiet_completion(check.MARKER.replace("\n","\r\n"),""))
        for output,errors in (("",""),(check.MARKER,"warning"),
                              (check.MARKER+"extra\n",""),(check.MARKER*2,"")):
            with self.subTest(output=output,errors=errors),self.assertRaises(ValueError):
                check.quiet_completion(output,errors)
    def test_import_inventory_includes_original_driver_and_current_helpers(self):
        helpers=check.imported_helpers()
        for path in (check.SELF,check.TEST,check.epoch.SELF,check.epoch.TEST,
                     "tools/p09/conservative_maintenance.py","tools/p09/current_issuer_build_inputs.py",
                     "tools/p09/weighted_audit_io.py"):
            self.assertIn(path,helpers)
    def invoke_synthetic_worker(self, mutate=None):
        task=check.task_for(992);target=check.target_for(992)
        env={name:"" for name in check.OVERRIDES}
        env.update(CARGO_BUILD_JOBS="1",RUSTUP_AUTO_INSTALL="0",
            CARGO_PROFILE_DEV_DEBUG_ASSERTIONS="true",CARGO_PROFILE_DEV_OVERFLOW_CHECKS="true")
        args=["cargo",*check.ARGS,"--locked","--offline","--jobs","1","--color=never",
              "--target-dir",str(target)]
        kwargs=dict(cwd=check.owned.ROOT,stdin=check.subprocess.DEVNULL,env=env)
        if mutate:mutate(args,kwargs)
        def fake_original_worker(_):return check.subprocess.call(args,**kwargs)
        stream=io.StringIO()
        with patch.object(check.subprocess,"call",return_value=0) as raw, \
             patch.object(check.owned,"worker",side_effect=fake_original_worker),redirect_stdout(stream):
            result=check.worker(task)
        return result,stream.getvalue(),raw.call_args
    def test_checked_worker_retains_assertions_and_disables_incremental(self):
        result,output,call=self.invoke_synthetic_worker()
        self.assertEqual(result,0);self.assertEqual(output,check.MARKER)
        self.assertEqual(call.kwargs["env"]["CARGO_INCREMENTAL"],"0")
        self.assertEqual(call.kwargs["env"]["CARGO_PROFILE_DEV_DEBUG_ASSERTIONS"],"true")
    def test_worker_rejects_argument_and_compiler_override_drift(self):
        for mutate in (lambda a,k:a.append("--release"),
                       lambda a,k:k["env"].update(RUSTFLAGS="unsafe override"),
                       lambda a,k:k["env"].update(CARGO_PROFILE_DEV_OVERFLOW_CHECKS="false")):
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):
                self.invoke_synthetic_worker(mutate)


if __name__ == "__main__":
    unittest.main()
