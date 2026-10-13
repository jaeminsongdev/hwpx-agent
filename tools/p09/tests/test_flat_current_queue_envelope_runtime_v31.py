"""Original whole14 controller contracts plus run003 invariants4."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_envelope_runtime_v31 as controller
MODULE,AST_PROOFS=controller.test_namespace()

class Tests(MODULE.Tests):
    def test_exact_run003_identity_and_old_run002_preserved(self):
        m=controller.M
        self.assertEqual(m.RETRY.task(160),"case160-current-r003-tests")
        self.assertEqual(m.RETRY.root_path(m.base.CONFIG),controller.attempt.ROOT)
        self.assertEqual(controller.PRIOR160.M.RETRY.task(160),"case160-current-r002-tests")
        self.assertEqual(controller.PRIOR160.attempt.STOPPED["path"],controller.attempt.original.STOPPED["path"])
    def test_whole_controller_metadata_inverse(self):
        self.assertTrue(all(p["original_entire_code_metadata_inverse"] for p in controller.CODE_PROOFS.values()))
        self.assertIn("-envelope-controller-preflight039.v1.json",controller.M.preflight_projection.__code__.co_consts)
        self.assertIn("-envelope-controller-preflight038.v1.json",controller.PRIOR160.M.preflight_projection.__code__.co_consts)
    def test_actual29_scope_and_unique_root003(self):
        self.assertEqual(len(controller.M.graph_value().binding.descriptors()),29)
        self.assertNotEqual(controller.M.RETRY.root_path(controller.M.base.CONFIG),controller.attempt.STOPPED["path"])
    def test_raw_source_namespaces_not_hidden(self):
        self.assertTrue(all(not p["actual_module_imported_or_sys_modules_hidden"] for p in controller.SOURCE_PROOFS))

if __name__=="__main__":unittest.main()
