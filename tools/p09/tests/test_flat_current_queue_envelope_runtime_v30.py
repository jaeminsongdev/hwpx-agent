"""Whole original14 controller contracts plus adopted26 run002 invariants4."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_envelope_runtime_v30 as controller
MODULE,AST_PROOFS=controller.test_namespace()

class Tests(MODULE.Tests):
    def test_exact_run002_identity_and_old_run001_preserved(self):
        m=controller.M
        self.assertEqual(m.RETRY.task(160),"case160-current-r002-tests")
        self.assertEqual(m.RETRY.root_path(m.base.CONFIG),controller.attempt.ROOT)
        self.assertEqual(controller.PRIOR160.PRIOR160.M.RETRY.task(160),"case160-current-r001-tests")
        self.assertIs(controller.RETRY,controller.PRIOR160.RETRY)

    def test_whole_controller_function_metadata_inverse(self):
        self.assertTrue(all(p["original_entire_code_metadata_inverse"] for p in controller.CODE_PROOFS.values()))
        self.assertIsNot(controller.M.only160.__globals__,controller.PRIOR160.M.only160.__globals__)
        self.assertIn("-envelope-controller-preflight038.v1.json",controller.M.preflight_projection.__code__.co_consts)
        self.assertIn("-envelope-controller-preflight037.v1.json",controller.PRIOR160.M.preflight_projection.__code__.co_consts)

    def test_actual26_scope_and_root001_not_selected(self):
        self.assertNotEqual(controller.M.RETRY.root_path(controller.M.base.CONFIG),controller.attempt.STOPPED["path"])
        self.assertEqual(len(controller.M.graph_value().binding.descriptors()),26)

    def test_raw_namespaces_not_imported_then_hidden(self):
        self.assertTrue(all(not p["actual_module_imported_or_sys_modules_hidden"] for p in controller.SOURCE_PROOFS))

if __name__=="__main__":unittest.main()
