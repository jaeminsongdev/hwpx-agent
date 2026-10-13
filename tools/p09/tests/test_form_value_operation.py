from pathlib import Path
import unittest
from tools.p09 import qualify_form_value_operation as q


class FormValueOperationGuards(unittest.TestCase):
    def test_whole_original_product_inverse_and_all_thirteen_sources_are_authentic(self):
        value=q.authority()
        self.assertTrue(value["original_13_sources_exact"])
        self.assertTrue(value["new_product_complete_inverse_byte_exact"])
        self.assertTrue(value["only_logical_product_library_uses_declared_archive"])

    def test_product_body_extra_export_or_archive_tamper_is_rejected(self):
        raw=q.public.bounded_bytes(q.ROOT/q.old.LIB,2*1024*1024)
        original=q.public.checked(q.ROOT/q.history.ARCHIVE,q.history.OLD_LIB)
        for changed in (raw+b"\n",raw.replace(q.history.DELTA,b"",1),raw+q.history.DELTA):
            with self.assertRaises(ValueError):q.history.original_product(changed,original)
        with self.assertRaises(ValueError):q.history.original_product(raw,original+b"\n")

    def test_source_view_is_bounded_and_does_not_admit_new_sources_cache_git_or_config(self):
        copied,manifest,origins=q.history.select()
        self.assertLessEqual(len(copied),1800)
        self.assertLessEqual(sum(map(len,copied.values())),64*1024*1024)
        self.assertEqual(set(copied),set(manifest))
        self.assertEqual(origins[q.old.LIB],q.history.ARCHIVE)
        for name,digest in q.history.PUBLIC_P04_INPUTS.items():
            self.assertEqual(manifest[name],digest)
            self.assertEqual(q.oracle.sha(copied[name]),digest)
        for name in copied:
            q.old.prior.history.relative(name)
            self.assertNotIn("p09-43",name.lower())
            self.assertNotIn("form_value_operation",name)

    def test_original_current_authority_legitimate_failure_is_not_archived_pass(self):
        with self.assertRaisesRegex(ValueError,"product_preparation_complete_inverse_invalid"):q.old.authority()

    def test_actual_compiled_protocol_rejects_skip_filter_missing_duplicate_or_extra(self):
        names=sorted(q.TESTS)
        good="\n".join(f"test {name} ... ok" for name in names)+"\ntest result: ok. 9 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1s\n"
        self.assertEqual(q.old.prior.protocol(good,q.TESTS,9)["passed"],9)
        for bad in (good.replace(names[0],names[1]),good.replace("... ok","... ignored",1),good.replace("0 filtered out","1 filtered out"),good+f"test {names[0]} ... ok\n"):
            with self.assertRaises(ValueError):q.old.prior.protocol(bad,q.TESTS,9)

    def test_evidence_boundary_rejects_private_originals_and_traversal(self):
        self.assertEqual(q.evidence_path(q.ROOT/q.CAPSULE),q.ROOT/q.CAPSULE)
        for path in (Path("relative.json"),q.ROOT/q.old.CAPSULE,q.ROOT/"implementation/p09/evidence/private/anything.json",q.ROOT/"implementation/p09/evidence/../evidence"/Path(q.CAPSULE).name):
            with self.assertRaises(ValueError):q.evidence_path(path)


if __name__=="__main__":unittest.main()
