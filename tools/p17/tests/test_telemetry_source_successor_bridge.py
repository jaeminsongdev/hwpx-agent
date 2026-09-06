from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/p15/validate_telemetry_contract.py"
SPEC = importlib.util.spec_from_file_location("telemetry_successor_bridge_test", PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
WIDGET_PATH = ROOT / "tools/p16/validate_widget_shell_successor.py"
WIDGET_SPEC = importlib.util.spec_from_file_location(
    "widget_source_successor_bootstrap_test", WIDGET_PATH
)
assert WIDGET_SPEC is not None and WIDGET_SPEC.loader is not None
WIDGET = importlib.util.module_from_spec(WIDGET_SPEC)
WIDGET_SPEC.loader.exec_module(WIDGET)


def source_locks() -> list[dict[str, str]]:
    contract = json.loads(
        (ROOT / "implementation/p15/p15-telemetry-contract-v1.json").read_text(
            encoding="utf-8"
        )
    )
    return contract["source_locks"]


class TelemetrySourceSuccessorBridgeTests(unittest.TestCase):
    def test_frozen_current_source_admits_exact_dependency_policy_successor(self) -> None:
        replacements = VALIDATOR.validate_current_source_qualification(
            ROOT, source_locks()
        )
        self.assertEqual(
            replacements["deny.toml"],
            (
                "1b7f0c7a65ba80242847fbb24483fa82708f28b361e425c76c48233d52073ef3",
                "a939acc670946e472480d5dde52b0bc19caa326abd14418e90b522deb03025bd",
            ),
        )

    def test_frozen_p16_contract_admits_exact_policy_successor(self) -> None:
        replacements = VALIDATOR.validate_frozen_p16_source_qualification(
            ROOT, source_locks()
        )
        self.assertEqual(
            replacements["crates/mcp-control-plane/src/policy.rs"],
            (
                "32513728470e18608d1eeff419e83ece628d6a9c4dd2a948c1c95012e97412ac",
                "b0b566a3bd753f9463c16bc384f73bdb1d91cde58a09c92c977ceb4348a79d53",
            ),
        )

    def test_frozen_p16_contract_digest_tamper_fails_closed(self) -> None:
        with patch.object(VALIDATOR, "P16_SOURCE_CONTRACT_SHA256", "0" * 64):
            self.assertEqual(
                VALIDATOR.validate_frozen_p16_source_qualification(
                    ROOT, source_locks()
                ),
                {},
            )

    def test_widget_lock_bootstrap_is_exact_and_history_bound(self) -> None:
        contract = json.loads(
            (ROOT / "implementation/p16/p16-widget-shell-contract-v1.json").read_text(
                encoding="utf-8"
            )
        )
        replacements = WIDGET.current_widget_replacements(ROOT, contract)
        self.assertEqual(
            replacements["tools/p15/tests/test_inspector_staging_contract.py"],
            (
                "b18cef25d92231df643cb4c23f7c06508d310aaa1191c014a559e34a67aac36f",
                "41f8fe1ab6c35d2d4895ba6b320a8d1bd1418c74ff5ee63fc3bd7945a7fb957a",
            ),
        )


if __name__ == "__main__":
    unittest.main()
