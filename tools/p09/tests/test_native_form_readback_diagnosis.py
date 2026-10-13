import copy
import json
from pathlib import Path
import unittest
from tools.p09 import diagnose_native_form_readback as q

class NativeReadbackDiagnosisTests(unittest.TestCase):
    def test_frozen_whole_recovery_has_fifteen_cases_and_seventy_five_files(self):
        value=json.loads(q.checked(q.ROOT/q.RECOVERY,q.RECOVERY_SHA))
        self.assertEqual(len(value["actual_native_batch"]["cases"]),15)
        self.assertEqual(len(q.native_pins(value)),75)
        self.assertFalse(value["claims"]["native_semantics_or_color_name_repair_qualified"])

    def test_duplicate_keys_are_rejected_and_canonical_order_is_stable(self):
        with self.assertRaisesRegex(ValueError,"diagnosis_duplicate_json_key"):
            json.loads('{"state":false,"state":true}',object_pairs_hook=q.duplicate_guard)
        self.assertEqual(q.canonical({"b":1,"a":2}),q.canonical({"a":2,"b":1}))

    def test_only_new_fixed_output_is_allowed(self):
        self.assertEqual(q.path_guard(q.ROOT/q.CAPSULE),q.ROOT/q.CAPSULE)
        for path in (q.ROOT/q.RECOVERY,q.ROOT/"implementation/p09/evidence/private/forged.json",
                     q.ROOT/"implementation/p09/evidence/../evidence/p09-47-native-readback-diagnosis.v1.json",Path("relative.json")):
            with self.assertRaisesRegex(ValueError,"diagnosis_output_boundary"):q.path_guard(path)

    def test_actual_rust_test_protocol_rejects_missing_extra_ignored_and_failure(self):
        valid='\n'.join(f'test tests::{name} ... ok' for name in sorted(q.RUST_TESTS))+'\ntest result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;\n'
        self.assertEqual(q.rust_test_protocol(valid.encode())["passed"],3)
        for text in (valid.replace('0 ignored','1 ignored'),valid.replace('0 failed','1 failed'),
                     valid.replace(' ... ok',' ... FAILED',1),valid+'test tests::unexpected ... ok\n'):
            with self.assertRaisesRegex(ValueError,"diagnosis_rust_test_protocol"):q.rust_test_protocol(text.encode())

    def test_native_pin_boundary_rejects_alias_and_partial_inventory(self):
        value=json.loads(q.checked(q.ROOT/q.RECOVERY,q.RECOVERY_SHA))
        partial=copy.deepcopy(value);partial["native_evidence_sha256"].pop(next(iter(partial["native_evidence_sha256"])))
        with self.assertRaisesRegex(ValueError,"diagnosis_native_inventory"):q.native_pins(partial)
        changed=copy.deepcopy(value);key=next(iter(changed["native_evidence_sha256"]))
        digest=changed["native_evidence_sha256"].pop(key);changed["native_evidence_sha256"]["../"+key]=digest
        with self.assertRaisesRegex(ValueError,"diagnosis_native_path_boundary"):q.native_pins(changed)

if __name__=="__main__":unittest.main()
