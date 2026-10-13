import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import list_case112_current_stored as listing


class ListingContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=json.loads((listing.c.ROOT/listing.BUILD_PIN["path"]).read_text(encoding="utf-8"))
    def test_real_passed_build_scope_requires_all_current_rust_and_preserved_inputs(self):
        expected,rust=listing.parent_scope(self.parent)
        self.assertEqual(len(expected),819);self.assertEqual(len(rust),787)
        self.assertIn(listing.catalog.ROOT,rust)
        self.assertNotIn(listing.EXE_PIN["path"],expected)
    def test_failure_or_runtime_or_cleanup_cannot_be_promoted_to_listing_admission(self):
        for change in (dict(state="STOPPED_NOT_ACCEPTED"),dict(current_build_binding_accepted=False),
                       dict(runtime_tests_executed=True),dict(cleanup_confirmed=False),dict(owned_tree_empty=False),
                       dict(compiled_artifact_byte_passes=1),dict(next_case=111),dict(accepted_count_delta=1)):
            row=copy.deepcopy(self.parent);row.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):listing.parent_scope(row)
    def test_binary_and_compiler_profile_are_exact(self):
        row=copy.deepcopy(self.parent);row["compiled_test_artifact_pin"]["sha256"]="a"*64
        with self.assertRaises(ValueError):listing.parent_scope(row)
        row=copy.deepcopy(self.parent);row["catalog_binding"]["catalog_profile"]["test"]=False
        with self.assertRaises(ValueError):listing.parent_scope(row)
        row=copy.deepcopy(self.parent);row["catalog_binding"]["catalog_profile"]["test"]=1
        with self.assertRaises(ValueError):listing.parent_scope(row)
    def test_inventory_cannot_omit_or_duplicate_current_source(self):
        for changed in (self.parent["source_freeze"][:-1],self.parent["source_freeze"]+[self.parent["source_freeze"][0]]):
            row=copy.deepcopy(self.parent);row["source_freeze"]=changed
            with self.assertRaises(ValueError):listing.parent_scope(row)
    def test_generation_closed_and_original_job_dispatch_retained(self):
        for run in (0,1000,True,"1"):
            with self.subTest(run=run),self.assertRaises(ValueError):listing.task_for(run)
        with self.assertRaises(ValueError):listing.run_for("arbitrary-tests")
        with patch.object(listing.build,"direct_path"),patch.object(listing.c,"worker",return_value=0) as original:
            self.assertEqual(listing.worker(listing.task_for(998)),0)
        original.assert_called_once_with(listing.task_for(998))
    def invoke_fake_worker(self,mutate=None):
        argv=["cargo",*listing.MARKER_ARGS,"--locked","--offline","--jobs","1","--color=never",
              "--target-dir",str(listing.build.TARGET)]
        kwargs=dict(cwd=listing.c.ROOT,stdin=listing.subprocess.DEVNULL,
            env=dict(RUST_TEST_THREADS="1",CARGO_PROFILE_TEST_DEBUG_ASSERTIONS="true",
                     CARGO_PROFILE_TEST_OVERFLOW_CHECKS="true"))
        if mutate:mutate(argv,kwargs)
        def original(_):return listing.subprocess.call(argv,**kwargs)
        with patch.object(listing.build,"direct_path"),patch.object(listing.subprocess,"call",return_value=0) as raw, \
             patch.object(listing.c,"worker",side_effect=original):
            result=listing.worker(listing.task_for(997))
        return result,raw.call_args
    def test_worker_can_only_execute_fixed_fresh_binary_full_list(self):
        result,call=self.invoke_fake_worker()
        self.assertEqual(result,0)
        self.assertEqual(call.args[0],[str(listing.c.ROOT/listing.EXE_PIN["path"]),"--list","--format=terse"])
        self.assertEqual(call.kwargs["env"]["RUST_TEST_NOCAPTURE"],"0")
        self.assertNotIn("--ignored",call.args[0]);self.assertNotIn("--exact",call.args[0])
    def test_worker_rejects_argument_and_assertion_environment_drift(self):
        for mutate in (lambda a,k:a.append("--exact"),lambda a,k:k["env"].update(RUST_TEST_THREADS="2"),
                       lambda a,k:k["env"].update(CARGO_PROFILE_TEST_OVERFLOW_CHECKS="false")):
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):self.invoke_fake_worker(mutate)


if __name__=="__main__":unittest.main()
