import copy
import io
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import run_optimized_signed_tests as subject


class OptimizedSignedTests(unittest.TestCase):
    def env(self):
        return {"CARGO_BUILD_JOBS":"1", "CARGO_PROFILE_TEST_OPT_LEVEL":"0",
            "CARGO_PROFILE_TEST_DEBUG_ASSERTIONS":"true", "CARGO_PROFILE_TEST_OVERFLOW_CHECKS":"true",
            "CARGO_PROFILE_TEST_CODEGEN_UNITS":"16", "RUST_TEST_THREADS":"1", "RUSTUP_AUTO_INSTALL":"0"}

    def args(self, task):
        tail = ["--",subject.previous.original.NAME,"--exact","--nocapture","--test-threads=1"] if task==subject.PROFILE else ["--","--list","--format","terse"]
        return ["cargo.exe",*subject.previous.original.ARGS,"--locked","--offline","--jobs","1",
            "--color=never","--target-dir",str(subject.maintenance.TARGET),*tail]

    def test_only_two_exact_packages_basic_level_one_and_lto_off(self):
        self.assertEqual(subject.PACKAGES,("hwpx-package","hwpx-agent-cli"))
        self.assertFalse(any("domain-ir" in arg for arg in subject.CONFIG))
        self.assertEqual(len(subject.CONFIG),11)
        self.assertEqual(subject.CONFIG[-1],'profile.test.lto="off"')
        self.assertFalse(any("*" in arg for arg in subject.CONFIG))

    def test_every_package_keeps_debug_assertions_overflow_codegen16_and_line_tables(self):
        for package in subject.PACKAGES:
            for key,value in (("opt-level","1"),("debug-assertions","true"),("overflow-checks","true"),("codegen-units","16"),("debug",'"line-tables-only"')):
                self.assertIn(f'profile.test.package.{package}.{key}={value}',subject.CONFIG)

    def test_exact_original_signed16_filter_nocapture_and_threads_retained(self):
        args=self.args(subject.PROFILE);actual=subject.optimized_arguments(args,subject.PROFILE,self.env())
        self.assertEqual(actual[23:],args[1:]);self.assertEqual(actual[-5:],args[-5:])
        self.assertEqual(actual[1:23],[x for entry in subject.CONFIG for x in ("--config",entry)])

    def test_inventory_lists_whole_original_target_without_runtime_filter(self):
        args=self.args(subject.INVENTORY);actual=subject.optimized_arguments(args,subject.INVENTORY,self.env())
        self.assertEqual(actual[23:],args[1:]);self.assertNotIn("--exact",actual)

    def test_mutated_jobs_offline_target_threads_or_filter_are_denied(self):
        args=self.args(subject.PROFILE)
        for token in ("--offline","1",str(subject.maintenance.TARGET),subject.previous.original.NAME,"--exact","--test-threads=1"):
            changed=list(args);changed[changed.index(token)]="foreign"
            with self.assertRaises(ValueError): subject.optimized_arguments(changed,subject.PROFILE,self.env())

    def test_original_check_environment_must_match_every_required_key(self):
        for key in self.env():
            changed=self.env();changed[key]="false"
            with self.assertRaises(ValueError): subject.optimized_arguments(self.args(subject.PROFILE),subject.PROFILE,changed)

    def test_finite_compile600_and_actual180_never_extend_original_full249_policy(self):
        for task,maximum in ((subject.INVENTORY,600),(subject.PROFILE,180)):
            for seconds in (30,maximum): subject.require_duration(task,seconds)
            for seconds in (True,29,maximum+1,1200,None):
                with self.assertRaises(ValueError): subject.require_duration(task,seconds)
        with self.assertRaises(ValueError): subject.require_duration("stored-form-tests",180)

    def test_inventory_requires_current_new_profile_receipt_before_original_full_guards(self):
        row={"source_variant":subject.SOURCE_VARIANT,"test_package_profile_config":list(subject.CONFIG),"task":subject.INVENTORY}
        with patch.object(subject.previous.original,"accept_inventory") as accepted:
            subject.accept_inventory(row,{},[],[])
        accepted.assert_called_once();self.assertEqual(accepted.call_args[0][0]["source_variant"],"call-local-xml-reuse-r9")

    def test_old_profile_or_config_or_task_is_never_current_compiled_qualification(self):
        row={"source_variant":subject.SOURCE_VARIANT,"test_package_profile_config":list(subject.CONFIG),"task":subject.INVENTORY}
        for key in row:
            bad=copy.deepcopy(row);bad[key]="foreign"
            with self.assertRaises(ValueError): subject.accept_inventory(bad,{},[],[])

    def test_inventory_selector_scope_is_explicit_and_bounded(self):
        self.assertTrue(subject.inventory_path(99).endswith("run99.v1.json"))
        for value in (True,0,100,"1"):
            with self.assertRaises(ValueError): subject.inventory_path(value)

    def test_worker_delegates_real_original_GO_job_gate_then_closed_override_only(self):
        captured=[]
        def original_worker(task):
            return subject.subprocess.call(self.args(task),cwd=subject.maintenance.ROOT,env=self.env(),stdin=subject.subprocess.DEVNULL)
        with patch.object(subject.previous,"run_worker",original_worker),patch.object(subject.subprocess,"call",lambda args,**kwargs: captured.append((args,kwargs)) or 7):
            self.assertEqual(subject.run_worker(subject.PROFILE),7)
        self.assertEqual(captured[0][0][23:],self.args(subject.PROFILE)[1:])
        self.assertEqual(captured[0][1]["env"],self.env())

    def test_actual_unchanged_worker_composition_and_maintenance_scope_restored(self):
        saved=subject.previous.PROFILE; captured=[]
        class Kernel:
            def GetCurrentProcess(self): return 1
            def IsProcessInJob(self, process, job, member):
                member._obj.value=True
                return True
        with patch.object(subject.maintenance,"Windows",return_value=SimpleNamespace(k=Kernel())), \
                patch.object(subject.maintenance.sys,"stdin",io.StringIO("P149_GO\n")), \
                patch.object(subject.maintenance.shutil,"which",return_value="cargo.exe"), \
                patch.object(subject.subprocess,"call",lambda args,**kwargs: captured.append(args) or 0):
            self.assertEqual(subject.run_worker(subject.PROFILE),0)
        for go,in_job in (("wrong\n",True),("P149_GO\n",False)):
            class DeniedKernel(Kernel):
                def IsProcessInJob(self, process, job, member):
                    member._obj.value=in_job
                    return True
            with patch.object(subject.maintenance,"Windows",return_value=SimpleNamespace(k=DeniedKernel())), \
                    patch.object(subject.maintenance.sys,"stdin",io.StringIO(go)), \
                    patch.object(subject.subprocess,"call") as denied:
                with self.assertRaises(ValueError): subject.run_worker(subject.PROFILE)
                denied.assert_not_called()
        self.assertEqual(subject.previous.PROFILE,saved)
        self.assertEqual(captured[0][-5:],["--",subject.previous.original.NAME,"--exact","--nocapture","--test-threads=1"])
        self.assertEqual(captured[0][1:23],[x for entry in subject.CONFIG for x in ("--config",entry)])
