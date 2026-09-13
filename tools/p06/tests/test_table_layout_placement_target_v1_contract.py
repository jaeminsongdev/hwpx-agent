from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "tools/p06/validate_table_layout_placement_target_v1_contract.py"
CONTRACT = ROOT / "protocol/private/p06-table-layout-placement-target-v1.json"


class TableLayoutPlacementTargetV1ContractTests(unittest.TestCase):
    def run_validator(self, contract: Path = CONTRACT) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(contract)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_current_contract_and_two_publications_pass(self) -> None:
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("state=pass", result.stdout)
        self.assertIn("features=10", result.stdout)
        self.assertIn("fixture_builds=3", result.stdout)
        self.assertIn("actual_hangul_2020=failed_open_input", result.stdout)

    def test_tampered_case_digest_fails_closed(self) -> None:
        value = json.loads(CONTRACT.read_text(encoding="utf-8"))
        value["cases"][0]["sha256"] = "0" * 64
        target_root = ROOT / "target"
        with tempfile.TemporaryDirectory(
            prefix="p06-layout-placement-contract-", dir=target_root
        ) as directory:
            path = Path(directory) / "contract.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            result = self.run_validator(path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture case differs", result.stderr)


if __name__ == "__main__":
    unittest.main()
