import unittest
from tools.p09 import qualify_current_native_form_diagnostic_admission_r03 as q
class CurrentDiagnosticRawTests(unittest.TestCase):
    def test_whole_raw_bytes_equal_and_non_bytes_changed_extra_missing_reject(self):
        q.raw_equal(b"{}",b"{}")
        for actual in (b"{}\n",b"",b"{}{}","{}",{},bytearray(b"{}"),None):
            with self.assertRaises(ValueError):q.raw_equal(actual,b"{}")
        with self.assertRaises(ValueError):q.raw_equal(b"{}","{}")
    def test_original_r02_receipt_and_every_raw_pin_preserved(self):
        import json
        value=json.loads(q.old.public.checked(q.ROOT/q.old.CAPSULE,q.OLD_SHA,2097152))
        for name,digest in value["source_sha256"].items():q.old.public.checked(q.ROOT/name,digest,2097152)
        self.assertFalse(value["claims"]["whole_old_authority_reexecuted"])
    def test_original_r02_verify_bug_is_retained_not_falsely_passed(self):
        with self.assertRaises(TypeError):q.old.exact(b"{}",b"{}","r02_probe")
    def test_only_fixed_new_paths_accept_not_original_or_private_or_traversal(self):
        self.assertEqual(q.path_guard(q.ROOT/q.CAPSULE,None),q.ROOT/q.CAPSULE)
        for path in (q.ROOT/q.old.CAPSULE,q.ROOT/q.old.COMPONENT,q.ROOT/"implementation/p09/evidence/private/x.json",
                     q.ROOT/"implementation/p09/evidence/../evidence/p09-36-native-form-diagnostic-current-admission.r03.json"):
            with self.assertRaises(ValueError):q.path_guard(path,None)
if __name__=="__main__":unittest.main()
