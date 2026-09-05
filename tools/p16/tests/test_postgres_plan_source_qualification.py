from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "postgres_plan_source_qualification.py"
SPEC = importlib.util.spec_from_file_location("p16_postgres_plan_source_qualification", SOURCE)
assert SPEC is not None and SPEC.loader is not None
qualification = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualification)


class PostgresPlanSourceQualificationTests(unittest.TestCase):
    def test_current_qualification_is_exact(self):
        contract = qualification.verify()
        self.assertTrue(contract["claims"]["authoritative_plan_source"])
        self.assertFalse(contract["claims"]["durable_plan_store"])

    def test_bounded_reader_rejects_escape_and_links(self):
        for value in ("../outside", "/absolute", "a\\b", "C:/outside", "a//b"):
            with self.subTest(value=value), self.assertRaises(qualification.QualificationError):
                qualification.read_bounded(qualification.ROOT, value)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root.parent / f"{root.name}-outside.json"
            outside.write_text("{}", encoding="utf-8")
            try:
                link = root / "link.json"
                try:
                    link.symlink_to(outside)
                except OSError:
                    return
                with self.assertRaises(qualification.QualificationError):
                    qualification.read_bounded(root, "link.json")
            finally:
                outside.unlink(missing_ok=True)

    def test_duplicate_receipt_keys_fail_closed(self):
        with self.assertRaises(qualification.QualificationError):
            qualification.load_json(b'{"decision":"PASS","decision":"FAIL"}')

    def test_contract_mutation_is_detected(self):
        observed = json.loads((qualification.ROOT / qualification.CONTRACT_PATH).read_text(
            encoding="utf-8"))
        observed["claims"]["phase_complete"] = True
        self.assertNotEqual(observed, qualification.expected_contract(qualification.ROOT))


if __name__ == "__main__":
    unittest.main()
