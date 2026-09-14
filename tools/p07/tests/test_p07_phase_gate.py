from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.p07 import validate_p07_phase_gate as validator


def copy_gate_files(root: Path) -> None:
    for relative in {validator.CONTRACT, validator.MIGRATION, validator.REPORT, *validator.SOURCES}:
        source = validator.ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


class P07PhaseGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.current_results = validator.collect_constituent_results()

    def test_current_gate_contract_passes_and_authorizes_p08(self) -> None:
        with patch.object(
            validator,
            "collect_constituent_results",
            return_value=deepcopy(self.current_results),
        ):
            value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_locks"], 12)
        self.assertEqual(value["validators_passed"], 10)
        self.assertEqual(value["tasks_closed"], 9)
        self.assertEqual(value["manual_review"], "user_attested")
        self.assertEqual(
            value["gate_state"],
            "pass_scoped_current_pc_hangul_2020_native_equation",
        )
        self.assertEqual(
            value["p08_authorization"],
            "authorized_current_pc_local_only",
        )
        self.assertFalse(value["product_complete"])

    def test_phase_derivation_requires_user_attested_layout_review(self) -> None:
        without_attestation = deepcopy(self.current_results)
        without_attestation["P07-07"]["manual_review"] = "not_run"
        self.assertEqual(validator.derive_phase(without_attestation)["closed_task_count"], 8)

        complete = deepcopy(without_attestation)
        complete["P07-07"]["manual_review"] = "user_attested"
        phase = validator.derive_phase(complete)
        self.assertEqual(phase["closed_task_count"], 9)
        self.assertEqual(
            phase["p07"], "pass_scoped_current_pc_hangul_2020_native_equation"
        )
        self.assertEqual(phase["p08_authorization"], "authorized_current_pc_local_only")

    def test_contract_decision_or_constituent_premature_promotion_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_gate_files(root)
            path = root / validator.CONTRACT
            contract = json.loads(path.read_text(encoding="utf-8"))
            contract["gate_decision"]["p07"] = "in_progress"
            path.write_text(json.dumps(contract), encoding="utf-8")
            with patch.object(
                validator,
                "collect_constituent_results",
                return_value=deepcopy(self.current_results),
            ):
                self.assertIn("gate_decision", validator.validate(root)["errors"])

        promoted = deepcopy(self.current_results)
        promoted["P07-07"]["manual_review"] = "not_run"
        with patch.object(
            validator,
            "collect_constituent_results",
            return_value=promoted,
        ):
            value = validator.validate()
        self.assertEqual(value["state"], "fail")
        self.assertTrue(
            {"constituent_result_P07-07", "closed_task_count", "manual_review", "phase_decision"}.issubset(
                value["errors"]
            )
        )

    def test_duplicate_contract_source_drift_and_validator_failure_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_gate_files(root)
            path = root / validator.CONTRACT
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace('"phase": "P07",', '"phase": "P07",\n  "phase": "P07",'),
                encoding="utf-8",
            )
            with patch.object(
                validator,
                "collect_constituent_results",
                return_value=deepcopy(self.current_results),
            ):
                self.assertIn("contract_json_or_path", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_gate_files(root)
            path = root / "WORK_BREAKDOWN_STRUCTURE.csv"
            path.write_bytes(path.read_bytes() + b"\nsource drift\n")
            with patch.object(
                validator,
                "collect_constituent_results",
                return_value=deepcopy(self.current_results),
            ):
                self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        failed = deepcopy(self.current_results)
        failed["P07-08"]["state"] = "fail"
        with patch.object(
            validator,
            "collect_constituent_results",
            return_value=failed,
        ):
            value = validator.validate()
        self.assertEqual(value["state"], "fail")
        self.assertIn("constituent_result_P07-08", value["errors"])


if __name__ == "__main__":
    unittest.main()
