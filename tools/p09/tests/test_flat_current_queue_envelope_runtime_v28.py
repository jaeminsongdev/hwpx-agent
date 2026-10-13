"""All original14 tests plus whole-code and strict-window inverse checks."""
from pathlib import Path
import sys
from types import FunctionType
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_envelope_runtime_v28 as controller

MODULE,AST_PROOFS=controller.test_namespace()


class Tests(MODULE.Tests):
    def test_whole_original_controller_code_metadata_inverse(self):
        self.assertGreaterEqual(len(controller.CODE_PROOFS),17)
        self.assertTrue(all(p["original_full_code_restored_by_metadata_inverse"] and
            p["original_defaults_closure_kwdefaults_retained"] for p in controller.CODE_PROOFS.values()))
        self.assertIsNot(controller.M.only160.__globals__,controller.PRIOR159.M.only159.__globals__)
        self.assertEqual(controller.PRIOR159.M.DATA,
            "implementation/p09/evidence/p09-361-case159-envelope-controller-data035.v1.json")

    def test_strict_window_entire_original_code_and_fifteen_seconds_retained(self):
        m=controller.M;check,proof=m.window.connect(m.prior.WINDOW_LINK.check_evidence)
        code=check.__code__
        restored=code.replace(co_consts=tuple(157 if type(x) is int and x==160 else x for x in code.co_consts))
        self.assertEqual(restored,m.prior.WINDOW_LINK.check_evidence.__code__)
        self.assertEqual(check.__defaults__,m.prior.WINDOW_LINK.check_evidence.__defaults__)
        self.assertEqual(check.__kwdefaults__,m.prior.WINDOW_LINK.check_evidence.__kwdefaults__)
        self.assertTrue(proof["original_fifteen_second_checks_retained"])
