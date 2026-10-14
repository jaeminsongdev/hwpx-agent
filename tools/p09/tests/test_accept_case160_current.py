"""Acceptance facade preconditions and declaration ordering; no writer."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

spec = importlib.util.spec_from_file_location("accept160", Path(__file__).parents[1]/"accept_case160_current.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def require(value, code):
    if not value: raise ValueError(code)


class Tests(unittest.TestCase):
    def test_closed_diagnostic_selection(self):
        for value in (True, 0, 9, "1", 1.0):
            with self.assertRaises(ValueError): module.diagnostic_path(value)
        self.assertTrue(module.diagnostic_path(1).endswith("attempt001.v2.json"))

    def test_wrong_epoch_rejected_before_acceptor_access(self):
        for config in (None, NS(index=159, before=153), NS(index=160, before=152)):
            with self.assertRaises(ValueError): module.facade(NS(require=require, base=NS(CONFIG=config)))

    def test_original_scope_failure_never_reads_witness_or_writes(self):
        calls=[]
        def prepare(q, pin): calls.append("whole"); raise ValueError("whole_original_failure")
        q=NS(json=lambda name:calls.append("witness"), pin=lambda name:calls.append("pin"))
        with self.assertRaises(ValueError):
            module.validated_prepare(q, module.ROOT, NS(API=NS(prepare=prepare)), NS())
        self.assertEqual(calls, ["whole"])


if __name__ == "__main__": unittest.main()
