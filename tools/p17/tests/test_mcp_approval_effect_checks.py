"""Unit guards for the P17-08 MCP approval-effect acceptance runner."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p17"))

import run_mcp_approval_effect_checks as checks  # noqa: E402


class McpApprovalEffectChecksTests(unittest.TestCase):
    def test_catalog_and_acceptance_checks_are_fixed_and_unique(self) -> None:
        self.assertEqual(len(checks.TOOLS), 7)
        self.assertEqual(len(set(checks.TOOLS)), 7)
        self.assertEqual(len(checks.CHECKS), 18)
        self.assertEqual(len(set(checks.CHECKS)), 18)
        self.assertEqual(checks.TOOLS[-2], checks.PREPARE_TOOL)
        self.assertEqual(checks.TOOLS[-1], checks.EXECUTE_TOOL)

    def test_test_authority_token_matches_rust_wire_shape_and_hmac(self) -> None:
        secret = b"0123456789abcdef0123456789abcdef"
        token = checks.mint_test_confirmation(
            secret=secret,
            token_id="cnf_acceptance01",
            operation_id="op_acceptance01",
            actor_sha256="a" * 64,
            tenant_sha256="b" * 64,
            target_sha256="c" * 64,
            plan_sha256="d" * 64,
            issued_at_unix_seconds=2_000_000_000,
        )
        prefix, encoded_payload, encoded_signature = token.split(".")
        self.assertEqual(prefix, "confirm_v1")
        payload_bytes = base64.urlsafe_b64decode(
            encoded_payload + "=" * (-len(encoded_payload) % 4)
        )
        signature = base64.urlsafe_b64decode(
            encoded_signature + "=" * (-len(encoded_signature) % 4)
        )
        self.assertTrue(
            hmac.compare_digest(
                signature, hmac.new(secret, payload_bytes, hashlib.sha256).digest()
            )
        )
        payload = json.loads(payload_bytes)
        self.assertEqual(
            list(payload),
            [
                "schema_version",
                "token_id",
                "operation_id",
                "actor_sha256",
                "tenant_sha256",
                "effect",
                "target_sha256",
                "plan_sha256",
                "issued_at_unix_seconds",
                "expires_at_unix_seconds",
                "user_confirmed",
            ],
        )
        self.assertEqual(payload["expires_at_unix_seconds"], 2_000_000_060)
        self.assertIs(payload["user_confirmed"], True)

    def test_bridge_has_no_confirmation_minting_surface(self) -> None:
        source = (ROOT / "web/local-companion-mcp/src/server.ts").read_text(
            encoding="utf-8"
        )
        package = json.loads(
            (ROOT / "web/local-companion-mcp/package.json").read_text(encoding="utf-8")
        )
        self.assertEqual(package["version"], "0.3.0")
        self.assertIn(checks.PREPARE_TOOL, source)
        self.assertIn(checks.EXECUTE_TOOL, source)
        self.assertNotIn("ConfirmationAuthority", source)
        self.assertNotIn("mint_test_confirmation", source)


if __name__ == "__main__":
    unittest.main()
