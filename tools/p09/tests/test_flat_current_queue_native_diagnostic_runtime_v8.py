import ast
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_native_diagnostic_runtime_v8 as v8


class Tests(unittest.TestCase):
    def test_entire_qualified_v7_AST_except_explicit_version_fields_and_added_duplicate_pin(self):
        root=v8.M.c.ROOT
        old=(root/"tools/p09/flat_current_queue_native_diagnostic_runtime_v7.py").read_text(encoding="utf-8")
        new=(root/v8.SELF).read_text(encoding="utf-8")
        translated=old.replace("_v7.py","_v8.py").replace("CONTROLLER_V7_","CONTROLLER_V8_")
        translated=translated.replace("controller/v7","controller/v8").replace("data007","data008")
        translated=translated.replace("preflight007","preflight008").replace("code9-r454","code2-r454b")
        translated=translated.replace("PASS_NATIVE_V7_NAMESPACE_AND_ORIGINAL_DATA_CONTROLLER9_NOT_PRODUCT",
                                      "PASS_NATIVE_V8_NO_EXTRA_ROOT_ACQUISITION_CODE2_NOT_PRODUCT")
        translated=translated.replace("contracts=dict(run=9,errors=0,failures=0,skipped=0),cleanup_confirmed=True,\n      actual_Native_product_controller_executed=False)",
                                      "contracts=dict(run=2,errors=0,failures=0,skipped=0),cleanup_confirmed=True,\n      actual_Native_product_controller_executed=False)")
        duplicate='    M.a.exact(q.pin(LEGACY146_PIN["path"]),LEGACY146_PIN,"ACTUAL_UNMODIFIED_LEGACY146")\n'
        self.assertEqual(translated.count(duplicate),1)
        expected=translated.replace(duplicate,"")
        self.assertEqual(ast.dump(ast.parse(expected),include_attributes=False),
                         ast.dump(ast.parse(new),include_attributes=False))

    def test_original_binding_root_read_and_strict_legacy_reread_and_native_membership_retained(self):
        pin=v8.M.V3.OLD.API.BASE_PIN
        raw=(v8.M.c.ROOT/pin["path"]).read_bytes()
        fn,proof=v8.M.V3.OLD.API.binding_projection(raw,replacement=v8.previous_validation)
        root=ast.parse(raw.decode("utf-8"))
        binding=next(n for n in root.body if isinstance(n,ast.FunctionDef) and n.name=="binding")
        self.assertIn("CONFIG.prior_candidate_pin",ast.unparse(binding))
        self.assertIn("a.read_exact(q, CONFIG.prior_candidate_pin)",ast.unparse(binding))
        current=ast.parse((v8.M.c.ROOT/v8.SELF).read_text(encoding="utf-8"))
        prev=next(n for n in current.body if isinstance(n,ast.FunctionDef) and n.name=="previous_validation")
        self.assertIn("M.a.read_exact(q, LEGACY146_PIN)",ast.unparse(prev))
        scope=next(n for n in current.body if isinstance(n,ast.FunctionDef) and n.name=="native_scope")
        self.assertIn("LEGACY146_PIN",ast.unparse(scope))
        self.assertTrue(proof["original_binding_AST_restored_exactly"])
        self.assertIs(v8._full_prepare.__globals__["data_path"],v8.M.data_path)


if __name__=="__main__":unittest.main()

