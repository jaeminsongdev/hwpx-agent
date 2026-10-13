import json
import unittest
from tools.p09 import record_native_form_color_preparation as q

class ColorPreparationProgressTests(unittest.TestCase):
    def test_two_unique_complete_original_root_inverses_and_all_predecessor_origins(self):
        value=q.preserve()
        self.assertEqual(len(value["two_complete_root_inverses"]),2)
        self.assertEqual(len(value["all_seventy_five_native_file_pins"]),75)
        self.assertFalse(value["whole_archived_predecessor_capsules_reexecuted"])

    def test_inverse_rejects_missing_duplicate_and_unrelated_body_change(self):
        for path,(_,_,delta) in q.CHANGED.items():
            raw=q.io.read(q.ROOT/path);q.inverse(path,raw)
            for changed in (raw.replace(delta,b"",1),raw+delta,raw+b"\n"):
                with self.assertRaisesRegex(ValueError,"color_progress_complete_inverse_changed"):q.inverse(path,changed)

    def test_test_protocol_rejects_filtered_ignored_failed_missing_and_extra_results(self):
        valid='\n'.join(f'test {name} ... ok' for name in sorted(q.PRODUCT_TESTS))+'\ntest result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;\n'
        self.assertEqual(q.rust_protocol(valid.encode(),q.PRODUCT_TESTS)["passed"],4)
        for value in (valid.replace('0 ignored','1 ignored'),valid.replace('0 filtered','1 filtered'),
                      valid.replace(' ... ok',' ... FAILED',1),valid+'test unexpected ... ok\n'):
            with self.assertRaisesRegex(ValueError,"color_progress_rust_protocol"):q.rust_protocol(value.encode(),q.PRODUCT_TESTS)

    def test_new_fixed_output_cannot_overwrite_original_or_private_receipts(self):
        self.assertEqual(q.target(q.ROOT/q.CAPSULE),q.ROOT/q.CAPSULE)
        for path in (*q.PREVIOUS,"implementation/p09/evidence/private/forged.json","implementation/p09/evidence/../evidence/p09-48-native-form-color-preparation.progress.v1.json"):
            with self.assertRaisesRegex(ValueError,"color_progress_output_boundary"):q.target(q.ROOT/path)

    def test_original_actual_preservation_failure_is_retained(self):
        with self.assertRaisesRegex(ValueError,"public_export_source_identity_changed"):q.original.progress.preserve()
        for path,(digest,_) in q.PREVIOUS.items():q.io.checked(q.ROOT/path,digest)

if __name__=="__main__":unittest.main()
