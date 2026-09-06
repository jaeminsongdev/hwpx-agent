from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p15"))

from validate_auth_tenant import (  # noqa: E402
    CONTRACT_PATH,
    EXPECTED_SOURCE_PATHS,
    RUST_PATH,
    sha256_file,
    validate_contract,
    validate_current_source_qualification,
)


class AuthTenantContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.rust_text = RUST_PATH.read_text(encoding="utf-8")

    def errors(self, contract: dict | None = None, rust_text: str | None = None) -> list[str]:
        return validate_contract(contract or self.contract, rust_text or self.rust_text, ROOT)

    def test_current_contract_passes(self) -> None:
        self.assertEqual(self.errors(), [])

    def test_official_source_is_exact(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["official_source"]["url"] = "https://example.invalid/auth"
        self.assertIn("official_source", self.errors(changed))

    def test_unknown_top_level_property_is_rejected(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["force_pass"] = True
        self.assertIn("top_level_keys", self.errors(changed))

    def test_public_and_service_boundaries_cannot_merge(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["boundary"]["service_tokens_accepted_from_openai_host"] = True
        self.assertIn("boundary", self.errors(changed))

    def test_production_jwks_cannot_be_claimed(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["boundary"]["production_jwks_implemented"] = True
        self.assertIn("boundary", self.errors(changed))

    def test_limits_are_locked(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["limits"]["user_token_lifetime_seconds"] += 1
        self.assertIn("limits", self.errors(changed))

    def test_scopes_are_exact_and_ordered(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["scopes"].reverse()
        self.assertIn("scopes", self.errors(changed))

    def test_required_behaviors_are_exact_and_ordered(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["required_behaviors"].reverse()
        self.assertIn("required_behaviors", self.errors(changed))

    def test_source_hash_drift_is_rejected(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["source_locks"][0]["sha256"] = "0" * 64
        self.assertIn("source_locks[0].sha256", self.errors(changed))

    def test_source_lock_order_is_exact(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["source_locks"].reverse()
        self.assertIn("source_locks.paths", self.errors(changed))

    def test_p14_supersession_validator_is_locked(self) -> None:
        for path in [
            "tools/p14/validate_cancel_cleanup.py",
            "tools/p14/validate_retention_local_mirror.py",
        ]:
            with self.subTest(path=path):
                index = EXPECTED_SOURCE_PATHS.index(path)
                changed = copy.deepcopy(self.contract)
                changed["source_locks"][index]["sha256"] = "0" * 64
                self.assertIn(f"source_locks[{index}].sha256", self.errors(changed))

    def test_current_retention_validator_successor_is_exactly_qualified(self) -> None:
        replacements = validate_current_source_qualification(
            ROOT, self.contract["source_locks"]
        )
        relative = "tools/p14/validate_retention_local_mirror.py"
        index = EXPECTED_SOURCE_PATHS.index(relative)
        expected = self.contract["source_locks"][index]["sha256"]
        observed = sha256_file(ROOT / relative)
        self.assertEqual(replacements.get(relative), (expected, observed))

    def test_security_critical_rust_token_is_required(self) -> None:
        changed = self.rust_text.replace("verify_slice(&signature)", "verify_slice(removed)", 1)
        self.assertTrue(any(error.startswith("rust_token:") for error in self.errors(rust_text=changed)))

    def test_private_key_material_is_forbidden(self) -> None:
        changed = f"{self.rust_text}\n// BEGIN PRIVATE KEY"
        self.assertIn("rust_forbidden:BEGIN PRIVATE KEY", self.errors(rust_text=changed))


if __name__ == "__main__":
    unittest.main()
