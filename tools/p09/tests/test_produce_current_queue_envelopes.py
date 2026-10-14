"""Only historical receipts may become explicitly named derivatives."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location("envelope_paths",Path(__file__).parents[1]/"produce_current_queue_envelopes.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class Tests(unittest.TestCase):
    def test_exact_historical_name(self):
        pin=dict(path="implementation/p09/evidence/p09-361-case160-current-runtime-run011.v1.json")
        self.assertTrue(module.output_path(pin,161).endswith("case160-runtime-run011.envelope.v1.json"))

    def test_source_current_case_and_bad_identity_rejected(self):
        for path in ("tools/p09/example.py","Cargo.toml","implementation/p09/evidence/p09-361-case161-current-runtime-run001.v1.json",
                     "implementation/p09/evidence/p09-361-case111-current-runtime-run001.v1.json",
                     "implementation/p09/evidence/p09-361-case160-current-runtime-run000.v1.json"):
            with self.assertRaises(ValueError):module.output_path(dict(path=path),161)

    def test_closed_context_and_pin_type(self):
        pin=dict(path="implementation/p09/evidence/p09-361-case160-current-runtime-run011.v1.json")
        for index in (True,160,250,"161",161.0):
            with self.assertRaises(ValueError):module.output_path(pin,index)
        for value in (None,[],dict(path=True)):
            with self.assertRaises(ValueError):module.output_path(value,161)


if __name__=="__main__":unittest.main()
