from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p09"))

from validate_form_control_hwpx_contract import (  # noqa: E402
    CONTRACT,
    QUALIFICATION,
    ContractError,
    load,
    validate,
)


class FormControlHwpxContractTests(unittest.TestCase):
    def test_contract_passes_without_target_promotion(self) -> None:
        result = validate()
        self.assertEqual(result["state"], "pass", result["errors"])
        self.assertEqual(result["integration_rows"], 2)
        self.assertTrue(result["static_section_hwpx"])
        self.assertEqual(result["actual_hangul"], "not_run")
        self.assertEqual(result["green_rows"], 0)

    def test_claim_promotion_fails_closed(self) -> None:
        contract = load(ROOT, CONTRACT)
        promoted = copy.deepcopy(contract)
        promoted["evidence_boundary"]["actual_hangul"] = True
        result = validate(contract_override=promoted)
        self.assertEqual(result["state"], "fail")
        self.assertIn("claim_promotion", result["errors"])

    def test_profile_and_feature_tamper_fail_closed(self) -> None:
        contract = load(ROOT, CONTRACT)
        changed = copy.deepcopy(contract)
        changed["profile"] = "unreviewed-profile"
        changed["feature_capabilities"]["REF-018"] = "ref.form_text"
        result = validate(contract_override=changed)
        self.assertEqual(result["state"], "fail")
        self.assertIn("identity", result["errors"])
        self.assertIn("features", result["errors"])

    def test_qualification_tamper_fails_closed(self) -> None:
        qualification = load(ROOT, QUALIFICATION)
        changed = copy.deepcopy(qualification)
        changed["claims"]["actual_hwpx"] = True
        result = validate(qualification_override=changed)
        self.assertEqual(result["state"], "fail")
        self.assertIn("qualification_claims", result["errors"])

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "duplicate.json"
            path.write_text('{"state":"pass","state":"green"}', encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "duplicate_json_key"):
                load(Path(temporary), "duplicate.json")


if __name__ == "__main__":
    unittest.main()
