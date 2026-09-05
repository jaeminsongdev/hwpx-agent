from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "postgres_durable_plan_qualification.py"
SPEC = importlib.util.spec_from_file_location("p16_postgres_durable_plan_qualification", SOURCE)
assert SPEC is not None and SPEC.loader is not None
qualification = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualification)


class PostgresDurablePlanQualificationTests(unittest.TestCase):
    def test_checked_in_contract_is_exact(self):
        contract = qualification.verify()
        self.assertTrue(contract["claims"]["durable_plan_store"])
        self.assertTrue(contract["claims"]["encrypted_at_rest"])
        self.assertFalse(contract["claims"]["actual_renderer"])
        self.assertFalse(contract["claims"]["phase_complete"])

    def test_receipt_rejects_duplicate_keys(self):
        with self.assertRaisesRegex(qualification.QualificationError, "json.duplicate"):
            qualification.load_json(b'{"decision":"PASS","decision":"FAIL"}')

    def test_bounded_reader_rejects_escape_and_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "inside.json").write_text("{}", encoding="utf-8")
            outside = root.parent / f"outside-{root.name}.json"
            outside.write_text("{}", encoding="utf-8")
            try:
                with self.assertRaises(qualification.QualificationError):
                    qualification.read_bounded(root, "../" + outside.name)
                link = root / "link.json"
                try:
                    link.symlink_to(outside)
                except OSError:
                    return
                with self.assertRaises(qualification.QualificationError):
                    qualification.read_bounded(root, "link.json")
            finally:
                outside.unlink(missing_ok=True)

    def test_receipt_cannot_promote_renderer_or_hangul(self):
        raw = qualification.read_bounded(qualification.ROOT, qualification.RECEIPT_PATH)
        receipt = json.loads(raw)
        self.assertTrue(receipt["durable_plan_store"])
        self.assertFalse(receipt["actual_renderer"])
        self.assertFalse(receipt["actual_hangul"])
        self.assertFalse(receipt["registered_host"])


if __name__ == "__main__":
    unittest.main()
