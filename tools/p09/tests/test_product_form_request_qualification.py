import json
from pathlib import Path
import unittest
from tools.p09 import qualify_product_form_request as q


class ProductFormRequestQualificationGuards(unittest.TestCase):
    def test_complete_predecessor_sources_and_current_failure_are_preserved(self):
        guard=q.progress.preserve()
        self.assertTrue(guard["original_eight_raw_sources_preserved"])
        self.assertTrue(guard["new_namespace_complete_inverse_exact"])
        self.assertEqual(guard["actual_original_current_guard"],
                         {"state":"fail","error_code":"form_operation_product_inverse_invalid","actually_invoked":True})
        with self.assertRaisesRegex(ValueError,"form_operation_product_inverse_invalid"):q.original.authority()

    def test_authentic_whole_original_view_has_only_declared_product_archive(self):
        copied,manifest,origins=q.history.select()
        self.assertEqual(len(manifest),1479)
        self.assertEqual(sum(map(len,copied.values())),49171201)
        self.assertEqual(set(copied),set(manifest))
        self.assertEqual(origins[q.progress.LIB],q.progress.ARCHIVE)
        for name,digest in manifest.items():
            self.assertEqual(q.oracle.sha(copied[name]),digest)
            self.assertEqual(origins[name],q.progress.ARCHIVE if name==q.progress.LIB else name)
            self.assertNotIn("p09-44",name);self.assertNotIn("form_product_request",name)
        self.assertEqual(copied[q.original.CAPSULE],q.public.checked(q.ROOT/q.original.CAPSULE,q.progress.PREDECESSOR_SHA,2*1024*1024))

    def test_original_local_progress_raw_receipt_and_six_pins_remain_exact(self):
        raw=q.public.checked(q.ROOT/q.progress.RECEIPT,q.PROGRESS_SHA,2*1024*1024)
        self.assertEqual(len(raw),3850)
        capsule=json.loads(raw,object_pairs_hook=q.oracle.duplicate_guard)
        self.assertEqual(set(capsule["source_sha256"]),set(q.progress.SOURCES))
        for name,digest in capsule["source_sha256"].items():q.public.checked(q.ROOT/name,digest,2*1024*1024)
        self.assertFalse(capsule["claims"]["full_source_successor_qualified"])
        self.assertFalse(capsule["claims"]["whole_original_p43_reexecuted"])

    def test_relative_paths_accept_frozen_windows_names_without_traversal_ads_or_cache(self):
        for name in ("crates/product-cli/src/lib.rs","implementation\\p09\\evidence\\private\\named\\saved.hwpx"):
            self.assertFalse(q.history.relative(name).is_absolute())
        for name in ("",None,42,"../x","x/../y","x\\..\\y","x//y","x/./y","/root","\\root",
                     "C:/root","C:\\root","x:ads","x/.git/config","target/x","x\\node_modules\\x","x/__pycache__/x"):
            with self.assertRaises(ValueError):q.history.relative(name)

    def test_whole_original_cli_result_rejects_missing_extra_false_or_different_fields(self):
        encode=lambda value:json.dumps(value).encode()
        good=q.history.EXPECTED_RESULT
        q.history.validate_result(0,encode(good),b"")
        bad=[{}, {**good,"extra":True}, {**good,"native_session_started":True},
             {**good,"qualification_sha256":"0"*64},{**good,"complete_original_p42_capsule_reexecuted":False},
             {**good,"native_session_started":0},{**good,"complete_original_p42_capsule_reexecuted":1}]
        for value in bad:
            with self.assertRaises(ValueError):q.history.validate_result(0,encode(value),b"")
        with self.assertRaises(ValueError):q.history.validate_result(1,encode(good),b"")
        with self.assertRaises(ValueError):q.history.validate_result(0,b"x"*(128*1024+1),b"")
        with self.assertRaises(ValueError):q.history.validate_result(0,encode(good),b"x"*(1024*1024+1))

    def test_compiled_inventory_rejects_missing_duplicate_ignored_filtered_and_extra_cases(self):
        names=sorted(q.progress.TESTS)
        good="\n".join(f"test {name} ... ok" for name in names)+"\ntest result: ok. 10 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1s\n"
        self.assertEqual(q.original.old.prior.protocol(good,q.progress.TESTS,10)["passed"],10)
        for bad in (good.replace(names[0],names[1]),good.replace("... ok","... ignored",1),
                    good.replace("0 filtered out","1 filtered out"),good+f"test {names[0]} ... ok\n",good.replace(f"test {names[0]} ... ok\n","",1)):
            with self.assertRaises(ValueError):q.original.old.prior.protocol(bad,q.progress.TESTS,10)
        guards=sorted(q.GUARDS)
        module="tools.p09.tests.test_product_form_request_qualification.ProductFormRequestQualificationGuards"
        lines=[f"{name} ({module}.{name}) ... ok" for name in guards]
        complete="\r\n".join(lines)+"\r\n\r\n----------------------------------------------------------------------\r\nRan 8 tests in 1.234s\r\n\r\nOK\r\n"
        self.assertEqual(q.guard_protocol(0,"",complete.encode())["passed"],8)
        for changed in (complete.replace(guards[0],guards[1]),complete.replace("... ok","... skipped",1),
                        complete.replace("Ran 8","Ran 7"),complete+lines[0],complete.replace(lines[0]+"\r\n","",1)):
            with self.assertRaises(ValueError):q.guard_protocol(0,"",changed.encode())
        with self.assertRaises(ValueError):q.guard_protocol(1,"",complete.encode())
        with self.assertRaises(ValueError):q.guard_protocol(0,"unexpected-output",complete.encode())

    def test_full_evidence_boundary_rejects_original_private_progress_and_traversal(self):
        self.assertEqual(q.evidence_path(q.ROOT/q.CAPSULE),q.ROOT/q.CAPSULE)
        for path in (Path("relative.json"),q.ROOT/q.progress.RECEIPT,q.ROOT/q.original.CAPSULE,
                     q.ROOT/"implementation/p09/evidence/private/anything.json",
                     q.ROOT/"implementation/p09/evidence/../evidence"/Path(q.CAPSULE).name):
            with self.assertRaises(ValueError):q.evidence_path(path)

    def test_source_inventory_requires_all_progress_sources_and_full_replay_tools(self):
        pins=q.source_pins()
        self.assertEqual(set(pins),set(q.SOURCES));self.assertEqual(len(pins),11)
        self.assertTrue(set(q.progress.SOURCES).issubset(pins))
        self.assertIn(q.progress.RECEIPT,pins)
        self.assertIn("tools/p09/reproduce_form_operation_pre_request.py",pins)
        self.assertIn("tools/p09/qualify_product_form_request.py",pins)


if __name__=="__main__":unittest.main()
