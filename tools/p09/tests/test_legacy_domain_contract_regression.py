from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest
from tools.p09 import qualify_legacy_domain_contract_regression as q


class LegacyDomainRegressionSuccessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = q.qualify()
        cls.archived = cls.actual["archived_contract_regression"]

    def view(self):
        temporary = tempfile.TemporaryDirectory(prefix="p09-39-negative-", dir=q.ROOT/"fixtures/target-build")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        copied, manifest = q.blueprint()
        q.prepare_view(root, copied, manifest)
        return root, copied, manifest

    def test_all_fifty_unchanged_contract_methods_and_actual_positive_baselines(self):
        result = self.archived["actual_isolated_test_result"]
        q.verify_result(result, self.archived["manifest"])
        self.assertEqual((result["passed"], result["positive_methods"], result["negative_methods"]), (50,10,40))
        self.assertEqual((result["validation_calls_observed"], result["subtests_observed"]), (146,109))
        self.assertEqual(len(result["baselines"]), 10)
        self.assertEqual(self.archived["copied_files"], 98)
        self.assertLess(self.archived["copied_bytes"], 2*1024*1024)
        self.assertTrue(self.archived["temporary_view_cleaned"])

    def test_current_public_api_is_really_reproduced_and_legacy_failures_preserved(self):
        self.assertTrue(self.actual["actual_current_public_capsule_byte_exact_reproduction"])
        suites = self.actual["actual_current_public_compiled_test_suites"]
        self.assertEqual([suites[key]["passed"] for key in ("domain","actual_capture","actual_library_unit")], [15,1,2])
        legacy = self.actual["actual_current_legacy_failures_preserved"]
        self.assertEqual((len(legacy),sum(row["state"]=="pass" for row in legacy),sum(row["state"]=="fail" for row in legacy)), (35,12,23))
        self.assertEqual(set(self.actual["actual_current_predecessor_failures_preserved"]), {"P09-37","P09-34-r02"})
        self.assertFalse(self.actual["claims"]["current_workspace_legacy_aggregate_pass"])

    def test_every_negative_call_uses_original_library_not_incidental_current_digest(self):
        result = self.archived["actual_isolated_test_result"]
        for record in result["tests"]:
            expected = "pass" if ".test_current_contract_" in record["name"] else "fail"
            self.assertEqual(record["observed_validator_state"], expected)
            self.assertEqual(record["observed_original_library_sha256"], q.current.OLD_LIB)
            self.assertGreater(record["validation_calls"], 0)
        for key, value in (("observed_validator_state","pass"), ("observed_original_library_sha256",q.current.CURRENT_LIB),
                           ("validation_calls",True), ("state","skip")):
            changed = copy.deepcopy(result)
            negative = next(row for row in changed["tests"] if ".test_current_contract_" not in row["name"])
            negative[key]=value
            with self.assertRaises(ValueError): q.verify_result(changed,self.archived["manifest"])

    def test_missing_duplicate_reordered_extra_and_skipped_result_inventory_rejects(self):
        result = self.archived["actual_isolated_test_result"]
        for records in (result["tests"][:-1],result["tests"]+[result["tests"][0]],list(reversed(result["tests"]))):
            changed=copy.deepcopy(result); changed["tests"]=records
            with self.assertRaises(ValueError): q.verify_result(changed,self.archived["manifest"])
        for key,value in (("skipped",1),("passed",True),("negative_methods",39),("current_workspace_legacy_aggregate_pass",True),
                          ("cargo_or_native_session_started",True),("validator_functions_or_defaults_replaced",True),("unknown_claim",False)):
            changed=copy.deepcopy(result); changed[key]=value
            with self.assertRaises(ValueError): q.verify_result(changed,self.archived["manifest"])
        for key in ("baselines","tests"):
            changed=copy.deepcopy(result); changed[key][0]=True
            with self.assertRaises(ValueError): q.verify_result(changed,self.archived["manifest"])
        changed=copy.deepcopy(result); changed["baselines"][0]["schema_version"]=True
        with self.assertRaises(ValueError): q.verify_result(changed,self.archived["manifest"])

    def test_coherent_total_and_per_method_call_count_forgery_rejects(self):
        result=self.archived["actual_isolated_test_result"]
        changed=copy.deepcopy(result); changed["tests"][0]["validation_calls"]-=1; changed["validation_calls_observed"]-=1
        with self.assertRaises(ValueError): q.verify_result(changed,self.archived["manifest"])
        changed=copy.deepcopy(result)
        changed["tests"][0]["validation_calls"]-=1; changed["tests"][1]["validation_calls"]+=1
        with self.assertRaises(ValueError): q.verify_result(changed,self.archived["manifest"])
        changed=copy.deepcopy(result); changed["tests"][0]["subtests_observed"]=True
        with self.assertRaises(ValueError): q.verify_result(changed,self.archived["manifest"])

    def test_outside_absolute_noncanonical_and_unknown_manifest_paths_rejects(self):
        for path in ("../escape","C:/escape","/absolute","part\\file","part//file","part/./file",""):
            with self.assertRaises(ValueError): q.worker.relative(path)
        root,_,manifest=self.view()
        changed=copy.deepcopy(manifest); changed["unknown_scope"]=True
        with self.assertRaises(ValueError): q.worker.snapshot(changed,root)
        changed=copy.deepcopy(manifest); changed["source_sha256"][q.current.LIB]=q.current.CURRENT_LIB
        with self.assertRaises(ValueError): q.worker.snapshot(changed,root)

    def test_complete_physical_snapshot_missing_modified_extra_and_current_library_rejects(self):
        for operation in ("missing","modified","extra","current_library"):
            root,_,manifest=self.view()
            if operation=="missing": (root/q.current.LIB).unlink()
            elif operation=="modified":
                path=root/"tools/p09/tests/test_form_control_contract.py"; path.write_bytes(path.read_bytes()+b" ")
            elif operation=="extra": (root/"unexpected-source.py").write_bytes(b"unapproved")
            else: (root/q.current.LIB).write_bytes((q.ROOT/q.current.LIB).read_bytes())
            with self.assertRaises((OSError,ValueError)): q.worker.snapshot(manifest,root)

    def test_original_test_inventory_no_positive_skip_or_body_filter(self):
        _,manifest=q.blueprint()
        self.assertEqual(len(manifest["test_names"]),50)
        raw=(q.ROOT/"tools/p09/tests/test_form_control_contract.py").read_bytes()
        names=q.worker.test_names(raw,"tools.p09.tests.test_form_control_contract")
        self.assertEqual(len(names),5)
        for changed in (raw.replace(b"def test_current_contract_",b"def disabled_current_contract_"),
                        raw.replace(b"def test_claim_promotion",b"def disabled_claim_promotion")):
            with self.assertRaises(ValueError): q.worker.test_names(changed,"tools.p09.tests.test_form_control_contract")

    def test_duplicate_worker_results_and_missing_isolation_rejects(self):
        for raw in ('{"state":"pass","state":"fail"}','{"nested":{"a":1,"a":2}}'):
            with self.assertRaises(ValueError): json.loads(raw,object_pairs_hook=q.worker.duplicate_guard)
        code,stdout=q.current.run([q.sys.executable,q.WORKER])
        self.assertEqual(code,2)
        self.assertEqual(json.loads(stdout),{"state":"fail","error_code":"legacy_view_python_isolation_required"})

    def test_privacy_native_batch_and_scoped_claims_not_workspace_or_product_pass(self):
        raw=q.q.shared.lifecycle.canonical_bytes(self.actual)
        for forbidden in (b"C:\\",b"D:\\","P09 실제 입력".encode(),b'"before"'):
            self.assertTrue(forbidden not in raw,"legacy_regression_plaintext_or_absolute_path_present")
        self.assertEqual(self.actual["future_native_diagnostic_batch"],{"cases":15,"stages":30,"state":"not_run","typed_only_inputs_added":0})
        for key in ("current_workspace_legacy_aggregate_pass","original_tests_or_validators_rewritten",
                    "source_locks_refreshed_or_validator_functions_replaced","archived_view_is_current_full_workspace_or_native_pass",
                    "native_input_output_qualified","production_routing_qualified","new_native_execution","p09_complete"):
            self.assertFalse(self.actual["claims"][key])


if __name__=="__main__":
    unittest.main()
