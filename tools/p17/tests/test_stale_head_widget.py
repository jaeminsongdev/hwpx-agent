from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools/p17/stale_head_widget.py"
SPEC = importlib.util.spec_from_file_location("stale_head_widget", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("stale-head module unavailable")
stale_head_widget = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stale_head_widget)


class StaleHeadWidgetTests(unittest.TestCase):
    def receipt(self) -> tuple[Path, dict[str, object]]:
        paths = sorted(
            (ROOT / "artifacts/p17/stale-head-widget-runs").glob("*/receipt.json")
        )
        self.assertTrue(paths)
        path = max(paths, key=lambda candidate: candidate.stat().st_mtime_ns)
        return path, json.loads(path.read_text(encoding="utf-8"))

    def test_current_receipt_is_bounded_component_evidence(self) -> None:
        path, receipt = self.receipt()
        self.assertEqual(stale_head_widget.validate_receipt(receipt, path), [])

    def test_receipt_cannot_promote_unregistered_host(self) -> None:
        path, receipt = self.receipt()
        tampered = copy.deepcopy(receipt)
        tampered["claims"]["project_conflict_resolve_registered"] = True
        self.assertIn(
            "receipt.contract",
            stale_head_widget.validate_receipt(tampered, path),
        )

    def test_receipt_rejects_injected_fields_and_path_identity_drift(self) -> None:
        path, receipt = self.receipt()
        injected = copy.deepcopy(receipt)
        injected["unexpected"] = "ignored-by-old-verifier"
        self.assertIn("receipt.keys", stale_head_widget.validate_receipt(injected, path))

        wrong_identity = copy.deepcopy(receipt)
        wrong_identity["run_id"] = "0" * 32
        self.assertIn(
            "receipt.path.identity",
            stale_head_widget.validate_receipt(wrong_identity, path),
        )

    def test_current_sources_and_bundle_are_bounded(self) -> None:
        self.assertEqual(stale_head_widget.validate_sources(), [])


if __name__ == "__main__":
    unittest.main()
