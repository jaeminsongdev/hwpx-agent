import json
import unittest
from pathlib import Path
from tools.p09 import record_stored_product_request_progress as q

class StoredProductRequestProgressGuards(unittest.TestCase):
    def test_original_whole_modules_seventeen_pins_and_1490_raw_origins_preserved(self):
        value=q.preserve()
        self.assertEqual(value["original_graph_files"],1490)
        self.assertEqual(value["original_graph_bytes"],49503833)
        self.assertTrue(value["two_unique_complete_original_module_inverses_exact"])
        self.assertFalse(value["whole_original_p45_reexecuted"])
        self.assertEqual(value["actual_current_p45_failure"]["state"],"fail")

    def test_unique_complete_inverses_reject_missing_duplicate_or_other_body_changes(self):
        for name,(file,digest) in q.CHANGED.items():
            original=q.public.checked(q.ROOT/(q.ARCHIVE+file),digest,2*1024*1024)
            current=q.public.bounded_bytes(q.ROOT/name,2*1024*1024);q.inverse(name,current,original)
            for bad in [original,current+b"\n",current+q.BINDING_DELTA,current.replace(b"Request",b"ChangedRequest")]:
                with self.assertRaises(ValueError):q.inverse(name,bad,original)

    def test_evidence_boundary_rejects_original_full_local_private_and_traversal(self):
        self.assertEqual(q.path_guard(q.ROOT/q.RECEIPT),q.ROOT/q.RECEIPT)
        for path in [q.ROOT/q.old.CAPSULE,q.ROOT/q.old.progress.RECEIPT,q.ROOT/"implementation/p09/evidence/private/progress.json",
                     q.ROOT/"implementation/p09/evidence/../evidence"/Path(q.RECEIPT).name]:
            with self.assertRaises(ValueError):q.path_guard(path)
        for key in ["../bad","C:/bad","a\\..\\bad","a:stream","/absolute"]:
            with self.assertRaises(ValueError):q.origin(key,{})

    def test_all_eight_actual_product_case_protocol_and_source_inventory_are_exact(self):
        good="\n".join(f"test {name} ... ok" for name in sorted(q.TESTS))+"\ntest result: ok. 8 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1.00s\n"
        self.assertEqual(q.old.old.original.old.prior.protocol(good,q.TESTS,8)["passed"],8)
        for bad in [good.replace(" ... ok"," ... ignored",1),good.replace(" ... ok"," ... FAILED",1),
                    good+"test extra ... ok\n",good.replace("0 filtered out","1 filtered out"),good.replace(sorted(q.TESTS)[0],"unexpected")]:
            with self.assertRaises(ValueError):q.old.old.original.old.prior.protocol(bad,q.TESTS,8)
        self.assertEqual(len(q.SOURCES),len(set(q.SOURCES)))
        original=json.loads(q.public.checked(q.ROOT/q.old.CAPSULE,q.CAPSULE_SHA,2*1024*1024))
        self.assertEqual(len(original["source_sha256"]),17)
        self.assertFalse(original["claims"]["p09_complete"])
        good_python="\n".join(f"{name} (tools.p09.tests.test_stored_product_request_progress.StoredProductRequestProgressGuards.{name}) ... ok" for name in sorted(q.GUARDS))+"\n\nRan 4 tests in 1.00s\n\nOK\n"
        self.assertEqual(q.guard_protocol(0,"",good_python.encode())["passed"],4)
        self.assertEqual(q.guard_protocol(0,"",good_python.replace("\n","\r\n").encode())["passed"],4)
        for bad in [good_python.replace(" ... ok"," ... skipped",1),good_python.replace(sorted(q.GUARDS)[0],"unexpected"),
                    good_python+"extra output",good_python.replace("Ran 4","Ran 3")]:
            with self.assertRaises(ValueError):q.guard_protocol(0,"",bad.encode())
        with self.assertRaises(ValueError):q.guard_protocol(1,"",good_python.encode())
        with self.assertRaises(ValueError):q.guard_protocol(0,"unexpected",good_python.encode())

if __name__=="__main__":unittest.main()
