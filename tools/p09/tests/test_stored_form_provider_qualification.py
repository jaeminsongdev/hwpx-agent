import json
from pathlib import Path
import unittest
from tools.p09 import qualify_stored_form_provider as q


class StoredFormProviderQualificationGuards(unittest.TestCase):
    def test_four_complete_inverses_original_sources_and_current_failure_remain_exact(self):
        guard=q.progress.preserve()
        self.assertTrue(guard["four_unique_complete_raw_inverses_exact"])
        self.assertTrue(guard["original_eleven_raw_sources_preserved"])
        self.assertTrue(guard["all_original_physical_view_raw_origins_preserved"])
        self.assertEqual(guard["actual_original_current_source_failure"],
                         {"state":"fail","error_code":"product_request_original_complete_inverse","actually_invoked":True})
        with self.assertRaisesRegex(ValueError,"product_request_original_complete_inverse"):q.old.qualify()

    def test_full_original_view_is_authentic_bounded_and_only_four_origins_are_archived(self):
        copied,manifest,origins=q.history.select()
        self.assertEqual(len(manifest),1490);self.assertEqual(sum(map(len,copied.values())),49503833)
        self.assertEqual(set(copied),set(manifest));self.assertEqual(sum(n!=actual for n,actual in origins.items()),4)
        for name,digest in manifest.items():
            self.assertEqual(q.oracle.sha(copied[name]),digest)
            self.assertEqual(origins[name],q.progress.ARCHIVE+q.progress.CHANGED[name][0] if name in q.progress.CHANGED else name)
            self.assertNotIn("p09-45",name);self.assertNotIn("form_stored_provider",name)
        self.assertEqual(copied[q.old.CAPSULE],q.public.checked(q.ROOT/q.old.CAPSULE,q.progress.CAPSULE_SHA,2*1024*1024))

    def test_original_local_progress_raw_receipt_and_all_twelve_pins_are_preserved(self):
        raw=q.public.checked(q.ROOT/q.progress.RECEIPT,q.PROGRESS_SHA,2*1024*1024);self.assertEqual(len(raw),4314)
        value=json.loads(raw,object_pairs_hook=q.oracle.duplicate_guard)
        self.assertEqual(set(value["source_sha256"]),set(q.progress.SOURCES))
        for name,digest in value["source_sha256"].items():q.public.checked(q.ROOT/name,digest,2*1024*1024)
        self.assertFalse(value["claims"]["full_source_successor_qualified"]);self.assertFalse(value["claims"]["whole_original_p44_reexecuted"])

    def test_paths_accept_original_windows_evidence_but_reject_unsafe_alias_components(self):
        for name in ("Cargo.lock","implementation\\p09\\evidence\\private\\named\\saved.hwpx"):
            self.assertFalse(q.history.relative(name).is_absolute())
        for name in ("",None,42,"../x","x/../y","x\\..\\y","x//y","x/./y","/root","\\root","C:/root","C:\\root",
                     "x:ads","x/.git/config","target/x","x\\node_modules\\x","x/__pycache__/x"):
            with self.assertRaises(ValueError):q.history.relative(name)

    def test_original_cli_result_rejects_missing_extra_mismatched_coerced_or_failed_output(self):
        encode=lambda value:json.dumps(value).encode();good=q.history.EXPECTED_RESULT
        q.history.validate_result(0,encode(good),b"")
        for value in ({},{**good,"extra":True},{**good,"native_session_started":True},{**good,"native_session_started":0},
                      {**good,"whole_original_p43_reexecuted":1},{**good,"qualification_sha256":"0"*64}):
            with self.assertRaises(ValueError):q.history.validate_result(0,encode(value),b"")
        with self.assertRaises(ValueError):q.history.validate_result(1,encode(good),b"")
        with self.assertRaises(ValueError):q.history.validate_result(0,b"x"*(128*1024+1),b"")
        with self.assertRaises(ValueError):q.history.validate_result(0,encode(good),b"x"*(1024*1024+1))

    def test_all_real_product_and_guard_protocols_reject_missing_duplicate_skip_filter_extra(self):
        names=sorted(q.progress.TESTS)
        good="\n".join(f"test {name} ... ok" for name in names)+"\ntest result: ok. 8 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1s\n"
        self.assertEqual(q.old.original.old.prior.protocol(good,q.progress.TESTS,8)["passed"],8)
        for bad in (good.replace(names[0],names[1]),good.replace("... ok","... ignored",1),good.replace("0 filtered out","1 filtered out"),
                    good+f"test {names[0]} ... ok\n",good.replace(f"test {names[0]} ... ok\n","",1)):
            with self.assertRaises(ValueError):q.old.original.old.prior.protocol(bad,q.progress.TESTS,8)
        guards=sorted(q.GUARDS);module="tools.p09.tests.test_stored_form_provider_qualification.StoredFormProviderQualificationGuards"
        lines=[f"{name} ({module}.{name}) ... ok" for name in guards]
        complete="\r\n".join(lines)+"\r\n\r\n----------------------------------------------------------------------\r\nRan 8 tests in 1.234s\r\n\r\nOK\r\n"
        self.assertEqual(q.guard_protocol(0,"",complete.encode())["passed"],8)
        for changed in (complete.replace(guards[0],guards[1]),complete.replace("... ok","... skipped",1),complete.replace("Ran 8","Ran 7"),
                        complete+lines[0],complete.replace(lines[0]+"\r\n","",1)):
            with self.assertRaises(ValueError):q.guard_protocol(0,"",changed.encode())
        with self.assertRaises(ValueError):q.guard_protocol(1,"",complete.encode())
        with self.assertRaises(ValueError):q.guard_protocol(0,"unexpected",complete.encode())

    def test_full_evidence_boundary_excludes_original_progress_private_and_traversal(self):
        self.assertEqual(q.evidence_path(q.ROOT/q.CAPSULE),q.ROOT/q.CAPSULE)
        for path in (Path("relative.json"),q.ROOT/q.old.CAPSULE,q.ROOT/q.progress.RECEIPT,q.ROOT/"implementation/p09/evidence/private/anything.json",
                     q.ROOT/"implementation/p09/evidence/../evidence"/Path(q.CAPSULE).name):
            with self.assertRaises(ValueError):q.evidence_path(path)

    def test_current_sdk_cargo_lock_failure_and_seventeen_source_pins_are_explicit(self):
        value=q.current_sdk_failure();self.assertEqual(value["rejected_repository_input"],"Cargo.lock")
        self.assertTrue(value["actually_invoked"]);self.assertTrue(value["blocked_class_bodies_not_counted_pass"])
        pins=q.source_pins();self.assertEqual(len(pins),17);self.assertEqual(set(pins),set(q.SOURCES))
        self.assertTrue(set(q.progress.SOURCES).issubset(pins));self.assertIn(q.progress.RECEIPT,pins)


if __name__=="__main__":unittest.main()
