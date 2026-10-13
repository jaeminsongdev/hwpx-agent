import copy
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import run_stored_signed_continuation as subject


class StoredSignedContinuationTests(unittest.TestCase):
    def names(self):
        return [subject.NAME, *(f"fixture::case_{n}" for n in range(248))]

    def output(self):
        return f"running 1 test\ntest {subject.NAME} ... ok\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 248 filtered out; finished in 1.00s\n"

    def inventory(self):
        pin = {"path":"bound.rs", "bytes":1, "sha256":"0"*64}
        names, modules = self.names(), [{"path":"bound.rs", "prefix":"fixture::"}]
        row = {"state":"PASS_SCOPED_NOT_GATE", "task":subject.INVENTORY,
            "compiled_inventory_exact":True, "source_variant":"call-local-xml-reuse-r9",
            "source_test_names":names, "source_module_instances":modules,
            "runtime_tests_executed":False, "product_complete":False, "P09_gate":"OPEN",
            "stop_reason":None, "owned_tree_empty":True, "cleanup_confirmed":True,
            "job_final":{"active_processes":0}, "source_freeze":[pin]}
        return row, {"bound.rs":pin}, names, modules

    def worker(self, task, go="P149_GO\n", in_job=True):
        class Kernel:
            def GetCurrentProcess(self):
                return 1
            def IsProcessInJob(self, process, job, member):
                member._obj.value = in_job
                return True
        calls = []
        def call(args, **kwargs):
            calls.append((args, kwargs))
            return 0
        with patch.object(subject.maintenance, "Windows", return_value=SimpleNamespace(k=Kernel())), \
                patch.object(subject.maintenance.sys, "stdin", io.StringIO(go)), \
                patch.object(subject.maintenance.shutil, "which", return_value="cargo"), \
                patch.object(subject.subprocess, "call", side_effect=call):
            result = subject.run_worker(task)
        return result, calls

    def test_selection_requires_all249_unique_names_and_one_exact_unchanged_case(self):
        names = self.names()
        self.assertEqual(subject.select_names(names), [subject.NAME])
        for bad in (names[:-1], [names[0]]*249, names[1:]+["foreign::test"], ["foreign::test"]*249):
            with self.assertRaises(ValueError):
                subject.select_names(bad)

    def test_complete_single_original_case_and_all248_filtered_are_required(self):
        subject.validate_output(self.output())
        for text in ("", self.output().replace(subject.NAME,"foreign::test"), self.output().replace("248 filtered", "0 filtered"), self.output().replace("1 passed", "0 passed")):
            with self.assertRaises(ValueError):
                subject.validate_output(text)

    def test_duplicate_ignored_failed_measured_or_oversized_output_cannot_pass(self):
        text = self.output()
        for bad in (text+text, text.replace("0 ignored", "1 ignored"), text.replace("0 failed", "1 failed"), text.replace("0 measured", "1 measured"), " "*32769):
            with self.assertRaises(ValueError):
                subject.validate_output(bad)

    def test_finite600_single_corpus_and180_inventory_do_not_change_parent_policy(self):
        before = copy.deepcopy(subject.maintenance.POLICY)
        for task, maximum in ((subject.CHANGED,600),(subject.INVENTORY,180)):
            for good in (30, maximum):
                subject.require_duration(task, good)
            for bad in (True,29,maximum+1,float(maximum)):
                with self.assertRaises(ValueError):
                    subject.require_duration(task,bad)
        with self.assertRaises(ValueError):
            subject.require_duration("foreign-tests",600)
        self.assertEqual(subject.maintenance.POLICY,before)

    def test_real_original_waiting_worker_only_adds_exact_selected_case(self):
        result, calls = self.worker(subject.CHANGED)
        self.assertEqual(result,0)
        self.assertEqual(len(calls),1)
        args, kwargs = calls[0]
        self.assertEqual(args[-4:],["--",subject.NAME,"--exact","--test-threads=1"])
        self.assertIn("--locked",args)
        self.assertIn("--offline",args)
        self.assertEqual(args[args.index("--jobs")+1],"1")
        self.assertEqual(kwargs["env"]["RUST_TEST_THREADS"],"1")
        self.assertEqual(kwargs["stdin"],subject.subprocess.DEVNULL)

    def test_real_original_waiting_inventory_worker_lists_only_no_runtime_cases(self):
        result, calls = self.worker(subject.INVENTORY)
        self.assertEqual(result,0)
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][0][-4:],["--","--list","--format","terse"])
        self.assertNotIn(subject.NAME,calls[0][0])
        self.assertNotIn("--test-threads=1",calls[0][0])

    def test_no_GO_or_no_owned_job_cannot_launch_any_cargo(self):
        for go, member in (("NO_GO\n",True),("P149_GO\n",False)):
            with self.assertRaises(ValueError):
                self.worker(subject.CHANGED,go,member)

    def test_compiled_full_inventory_requires_current_entire_source_and_helpers(self):
        row, expected, names, modules = self.inventory()
        subject.accept_inventory(row,expected,names,modules)
        bad = copy.deepcopy(row)
        bad["source_freeze"][0]["sha256"]="1"*64
        with self.assertRaises(ValueError):
            subject.accept_inventory(bad,expected,names,modules)

    def test_old_partial_dirty_or_runtime_inventory_is_not_current_compilation(self):
        row, expected, names, modules = self.inventory()
        for key,value in (("state","STOPPED_NOT_ACCEPTED"),("compiled_inventory_exact",False),
                ("runtime_tests_executed",True),("cleanup_confirmed",False),("owned_tree_empty",False),
                ("job_final",{"active_processes":1}),("source_test_names",names[:-1]),
                ("source_module_instances",[]),("source_variant","r8"),("stop_reason","STOP_DURATION_LIMIT")):
            with self.assertRaises(ValueError):
                subject.accept_inventory(dict(row,**{key:value}),expected,names,modules)

    def test_missing_capture_or_result_cannot_become_scoped_pass(self):
        row=subject.annotate({"task":subject.CHANGED,"state":"PASS_SCOPED_NOT_GATE","tests_passed":1},subject.CHANGED,self.names(),[],False)
        self.assertEqual(row["state"],"STOPPED_NOT_ACCEPTED")
        self.assertFalse(row["signed_changed16_component_complete"])
        captured=io.StringIO()
        def run(task,destination,seconds):
            json.dump({"task":task,"state":"PASS_SCOPED_NOT_GATE","tests_passed":1},captured)
            return 0
        with patch.object(subject.maintenance,"run",side_effect=run):
            subject.run_owned("fixture",{},self.names(),[],subject.CHANGED,600)
        self.assertEqual(json.loads(captured.getvalue())["state"],"STOPPED_NOT_ACCEPTED")

    def test_whole249_SQL_native_gate_freeze_and_publication_are_never_claimed(self):
        for task in subject.TASKS:
            row=subject.annotate({"task":task,"state":"PASS_SCOPED_NOT_GATE","tests_passed":1},task,self.names(),[],True)
            for key in ("full249_current_qualified","signed_SQL_native_or_Gate_qualified","product_complete","PC_freeze_resolved","original_test_bodies_changed","resource_policy_changed"):
                self.assertFalse(row[key])
            self.assertEqual(row["P09_gate"],"OPEN")
            self.assertEqual(row["signed_changed16_component_complete"],task==subject.CHANGED)
        with self.assertRaises(ValueError):
            subject.annotate({"task":"foreign"},subject.CHANGED,self.names(),[],True)

    def test_inventory_reference_is_explicit_bounded_run_not_latest_or_foreign(self):
        self.assertTrue(subject.inventory_path(1).endswith("inventory-run01.v1.json"))
        self.assertTrue(subject.inventory_path(99).endswith("inventory-run99.v1.json"))
        for bad in (0,100,True,"latest",-1):
            with self.assertRaises(ValueError):
                subject.inventory_path(bad)
