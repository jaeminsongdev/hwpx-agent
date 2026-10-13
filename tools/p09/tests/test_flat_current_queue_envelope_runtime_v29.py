"""Original14 controller tests plus actual reviewed run002 invariants4."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_envelope_runtime_v29 as controller
MODULE,AST_PROOFS=controller.test_namespace()

class Tests(MODULE.Tests):
    def test_exact_run002_identity_and_old_run001_preserved(self):
        m=controller.M
        self.assertEqual(m.RETRY.task(160),"case160-current-r002-tests")
        self.assertEqual(m.RETRY.root_path(m.base.CONFIG),controller.attempt.ROOT)
        self.assertEqual(controller.PRIOR160.M.RETRY.task(160),"case160-current-r001-tests")
    def test_whole_controller_function_metadata_inverse(self):
        self.assertTrue(all(p["original_entire_code_metadata_inverse"] for p in controller.CODE_PROOFS.values()))
        self.assertIsNot(controller.M.only160.__globals__,controller.PRIOR160.M.only160.__globals__)
    def test_root001_never_selected_for_new_run(self):
        self.assertNotEqual(controller.M.RETRY.root_path(controller.M.base.CONFIG),controller.attempt.STOPPED["path"])
    def test_raw_namespaces_not_imported_then_hidden(self):
        self.assertTrue(all(not p["actual_module_imported_or_sys_modules_hidden"] for p in controller.SOURCE_PROOFS))
