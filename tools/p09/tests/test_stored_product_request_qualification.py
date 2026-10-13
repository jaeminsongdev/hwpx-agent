import json
from pathlib import Path
import tempfile
import unittest
from tools.p09 import qualify_stored_product_request as q

class StoredProductRequestQualificationGuards(unittest.TestCase):
    def test_frozen_local_receipt_and_all_nine_sources_remain_immutable(self):
        raw=q.public.checked(q.ROOT/q.progress.RECEIPT,q.PROGRESS_SHA,2*1024*1024)
        self.assertEqual(len(raw),4641);local=json.loads(raw,object_pairs_hook=q.oracle.duplicate_guard)
        self.assertEqual(set(local["source_sha256"]),set(q.progress.SOURCES))
        self.assertEqual(len(local["source_sha256"]),9)
        for name,digest in local["source_sha256"].items():q.public.checked(q.ROOT/name,digest,2*1024*1024)
        self.assertFalse(local["claims"]["full_source_qualified"])
        self.assertFalse(local["claims"]["whole_original_p45_reexecuted"])
        self.assertEqual(local["actual_product_tests"]["passed"],8)
        self.assertEqual(local["actual_python_guards"]["passed"],4)

    def test_complete_original_view_is_authentic_bounded_with_only_two_archive_origins(self):
        base=q.history.scratch_parent()
        self.assertEqual(base,q.ROOT/"target")
        self.assertEqual(q.history.SCRATCH_PREFIX,"p46-")
        with tempfile.TemporaryDirectory(prefix=q.history.SCRATCH_PREFIX,dir=base) as temporary:
            directory=Path(temporary)
            self.assertTrue(q.history.scratch_boundary(directory,base))
            with self.assertRaises(ValueError):q.history.scratch_boundary(directory,q.ROOT/"fixtures/target-build")
            with self.assertRaises(ValueError):q.history.scratch_boundary(base,base)
            (directory/"nonempty").mkdir()
            with self.assertRaises(ValueError):q.history.scratch_boundary(directory,base)
        self.assertFalse(directory.exists())
        copied,manifest,origins=q.history.select()
        self.assertEqual(len(manifest),1521);self.assertEqual(sum(map(len,copied.values())),50450812)
        self.assertEqual(len(q.history.MIGRATIONS),17)
        self.assertEqual(sum(len(copied[name]) for name in q.history.MIGRATIONS),517795)
        self.assertTrue(all(manifest[name]==digest and origins[name]==name for name,digest in q.history.MIGRATIONS.items()))
        self.assertEqual({name for name,origin in origins.items() if name!=origin},set(q.progress.CHANGED))
        self.assertLessEqual(len(manifest),q.history.LIMIT_FILES)
        self.assertLessEqual(sum(map(len,copied.values())),q.history.LIMIT_BYTES)
        self.assertTrue(all(len(value)<=q.history.SOURCE_BYTES for value in copied.values()))
        self.assertFalse(any("p09-46" in name or "form_stored_product_request" in name or "form_product_request/stored.rs" in name for name in manifest))
        for name,raw in copied.items():
            self.assertEqual(q.oracle.sha(raw),manifest[name]);q.public.checked(q.ROOT/origins[name],manifest[name],q.history.SOURCE_BYTES)
        self.assertEqual(copied[q.old.CAPSULE],q.public.checked(q.ROOT/q.old.CAPSULE,q.progress.CAPSULE_SHA,2*1024*1024))

    def test_post_provider_pins_override_pre_provider_root_cargo_lock_and_getters(self):
        raw=q.public.checked(q.ROOT/q.old.CAPSULE,q.progress.CAPSULE_SHA,2*1024*1024)
        original=json.loads(raw,object_pairs_hook=q.oracle.duplicate_guard)
        graph=original["complete_original_product_request_reproduction"]["source_sha256"]
        copied,manifest,origins=q.history.select()
        for name in q.old.progress.CHANGED:
            self.assertNotEqual(graph[name],original["source_sha256"][name])
            self.assertEqual(manifest[name],original["source_sha256"][name])
            self.assertEqual(origins[name],name)
            self.assertEqual(copied[name],q.public.checked(q.ROOT/name,manifest[name],2*1024*1024))
        self.assertEqual(set(original["source_sha256"]),set(q.old.SOURCES))

    def test_all_original_modules_pins_and_graph_origins_preserved_with_current_failure(self):
        value=q.progress.preserve()
        self.assertEqual(value["original_graph_files"],1490)
        self.assertEqual(value["original_graph_bytes"],49503833)
        self.assertTrue(value["original_seventeen_raw_pins_preserved"])
        self.assertEqual(value["actual_current_p45_failure"]["state"],"fail")
        for name,(file,digest) in q.progress.CHANGED.items():
            original=q.public.checked(q.ROOT/(q.progress.ARCHIVE+file),digest,2*1024*1024)
            current=q.public.bounded_bytes(q.ROOT/name,2*1024*1024);q.progress.inverse(name,current,original)
            with self.assertRaises(ValueError):q.progress.inverse(name,current+b"\n",original)

    def test_original_cli_result_rejects_missing_extra_coerced_duplicate_failed_or_large_output(self):
        compile(q.history.P44_DIAGNOSTIC,"bounded_original_p44_diagnostic","exec")
        self.assertIn("diagnostic_only_original_p44_not_p45_qualification",q.history.P44_DIAGNOSTIC)
        self.assertIn("result=r.reproduce()",q.history.P44_DIAGNOSTIC)
        self.assertNotIn("print(process.stdout",q.history.P44_DIAGNOSTIC)
        compile(q.history.P42_DIAGNOSTIC,"bounded_original_p42_diagnostic","exec")
        self.assertIn("value=q.qualify()",q.history.P42_DIAGNOSTIC)
        self.assertIn("raw==original",q.history.P42_DIAGNOSTIC)
        self.assertNotIn("print(value)",q.history.P42_DIAGNOSTIC)
        code=q.history.P42_DIAGNOSTIC
        for module in ("reproduce_form_preparation_pre_operation","reproduce_form_operation_pre_request",
                       "reproduce_product_request_pre_stored_provider"):
            code=q.history.diagnostic_layer_code(module,code)
            compile(code,"authentic_diagnostic_layer","exec")
            self.assertIn("r.select()",code)
            self.assertNotIn("r.ROOT=",code)
        with self.assertRaises(ValueError):q.history.diagnostic_layer_code("untrusted_module",code)
        expected=q.history.EXPECTED_RESULT;good=json.dumps(expected).encode()
        q.history.validate_result(0,good,b"")
        for value in [{key:value for key,value in expected.items() if key!="source_pins"},
                      {**expected,"extra":True},{**expected,"whole_original_p44_reexecuted":1},
                      {**expected,"native_session_started":0},{**expected,"source_pins":17.0},
                      {**expected,"qualification_sha256":"0"*64},{**expected,"state":"fail"}]:
            with self.assertRaises(ValueError):q.history.validate_result(0,json.dumps(value).encode(),b"")
        with self.assertRaises(ValueError):q.history.validate_result(1,good,b"")
        with self.assertRaises(ValueError):q.history.validate_result(0,b'{"state":"pass",'+good[1:],b"")
        with self.assertRaises(ValueError):q.history.validate_result(0,good+b"{}",b"")
        with self.assertRaises(ValueError):q.history.validate_result(0,b" "*(128*1024+1),b"")
        with self.assertRaises(ValueError):q.history.validate_result(0,good,b" "*(1024*1024+1))

    def test_actual_product_and_python_protocols_reject_missing_extra_ignore_filter_skip(self):
        good="\n".join(f"test {name} ... ok" for name in sorted(q.progress.TESTS))+"\ntest result: ok. 8 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1.00s\n"
        self.assertEqual(q.prior.protocol(good,q.progress.TESTS,8)["passed"],8)
        for bad in [good.replace(" ... ok"," ... ignored",1),good.replace(" ... ok"," ... FAILED",1),
                    good+"test extra ... ok\n",good.replace("0 filtered out","1 filtered out"),good.replace(sorted(q.progress.TESTS)[0],"unexpected")]:
            with self.assertRaises(ValueError):q.prior.protocol(bad,q.progress.TESTS,8)
        py="\n".join(f"{name} (tools.p09.tests.test_stored_product_request_qualification.StoredProductRequestQualificationGuards.{name}) ... ok" for name in sorted(q.GUARDS))+"\n\nRan 8 tests in 1.00s\n\nOK\n"
        self.assertEqual(q.guard_protocol(0,"",py.encode())["passed"],8)
        self.assertEqual(q.guard_protocol(0,"",py.replace("\n","\r\n").encode())["passed"],8)
        for bad in [py.replace(" ... ok"," ... skipped",1),py.replace(sorted(q.GUARDS)[0],"unexpected"),
                    py+"extra",py.replace("Ran 8","Ran 7"),py.replace(" ... ok"," ... ERROR",1)]:
            with self.assertRaises(ValueError):q.guard_protocol(0,"",bad.encode())
        with self.assertRaises(ValueError):q.guard_protocol(1,"",py.encode())
        with self.assertRaises(ValueError):q.guard_protocol(0,"extra",py.encode())

    def test_full_evidence_and_windows_paths_reject_original_private_traversal_and_aliases(self):
        self.assertEqual(q.evidence_path(q.ROOT/q.CAPSULE),q.ROOT/q.CAPSULE)
        for path in [q.ROOT/q.progress.RECEIPT,q.ROOT/q.old.CAPSULE,q.ROOT/"implementation/p09/evidence/private/proof.json",
                     q.ROOT/"implementation/p09/evidence/../evidence/p09-46-stored-product-request.source-qualified.v1.json"]:
            with self.assertRaises(ValueError):q.evidence_path(path)
        self.assertEqual(q.history.relative("implementation\\p09\\evidence\\proof.json"),q.history.relative("implementation/p09/evidence/proof.json"))
        for path in ["../bad","a\\..\\bad","C:/bad","a:stream","/absolute","a/.git/b","a/target/b","a/node_modules/b"]:
            with self.assertRaises(ValueError):q.history.relative(path)
        self.assertEqual(len(q.source_pins()),31)

    def test_current_old_and_sdk_failures_identify_distinct_changed_inputs_and_scope(self):
        failure=q.current_original_failure();sdk=q.old.current_sdk_failure()
        self.assertEqual(failure["rejected_repository_input"],"crates/product-cli/src/form_product_request.rs")
        self.assertEqual(sdk["rejected_repository_input"],"Cargo.lock")
        self.assertTrue(failure["actually_invoked"] and sdk["actually_invoked"])
        self.assertEqual(failure["state"],sdk["state"])
        original=json.loads(q.public.checked(q.ROOT/q.old.CAPSULE,q.progress.CAPSULE_SHA,2*1024*1024))
        for claim in ["p09_complete","cli_form_action_enabled","signed_form_authority_or_execution_manifest",
                      "atomic_cas_execution_idempotency","full_document_import"]:self.assertFalse(original["claims"][claim])
        self.assertFalse(original["privacy"]["native_session_started"])
        self.assertTrue(original["claims"]["normal_artifact_service_read_audit_emitted"])

if __name__=="__main__":unittest.main()
