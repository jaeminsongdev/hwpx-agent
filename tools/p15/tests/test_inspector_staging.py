from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, relative: str):
    specification = importlib.util.spec_from_file_location(name, ROOT / relative)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


staging = load_module("p15_inspector_staging", "tools/p15/run_inspector_staging.py")


class InspectorStagingTests(unittest.TestCase):
    def test_synthesized_inputs_validate_for_all_eighteen_tools(self) -> None:
        catalog = json.loads(staging.CATALOG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(catalog["descriptor_count"], 18)
        for index, descriptor in enumerate(catalog["tools"], start=1):
            arguments = staging.synthesize(descriptor["inputSchema"])
            arguments["request_id"] = f"req_inspector_{index:02d}"
            Draft202012Validator(descriptor["inputSchema"]).validate(arguments)

    def test_generated_token_has_expected_bounded_public_claims(self) -> None:
        secret = bytes(range(32))
        token = staging.make_token(secret, 2_000_000_000)
        segments = token.split(".")
        self.assertEqual(len(segments), 3)

        def decode(segment: str):
            padded = segment + "=" * (-len(segment) % 4)
            return json.loads(base64.urlsafe_b64decode(padded))

        header = decode(segments[0])
        claims = decode(segments[1])
        self.assertEqual(header, {"alg": "HS256", "kid": "local-key-01", "typ": "at+jwt"})
        self.assertEqual(claims["aud"], staging.RESOURCE)
        self.assertEqual(claims["sub"], staging.SUBJECT)
        self.assertEqual(claims["token_kind"], "user")
        self.assertEqual(claims["exp"] - claims["iat"], 660)
        self.assertNotIn("service_id", claims)

    def test_tool_list_requires_exact_order_and_schemas(self) -> None:
        catalog = json.loads(staging.CATALOG_PATH.read_text(encoding="utf-8"))
        listed = {
            "tools": [
                {
                    "name": descriptor["name"],
                    "inputSchema": descriptor["inputSchema"],
                    "outputSchema": descriptor["outputSchema"],
                    "annotations": descriptor["annotations"],
                    "_meta": descriptor["_meta"],
                }
                for descriptor in catalog["tools"]
            ]
        }
        self.assertEqual(
            staging.validate_tool_list(listed, catalog),
            [descriptor["name"] for descriptor in catalog["tools"]],
        )
        listed["tools"].reverse()
        with self.assertRaises(staging.AcceptanceError):
            staging.validate_tool_list(listed, catalog)

    def test_diagnostics_redact_bearer_tokens(self) -> None:
        token = "a" * 24 + "." + "b" * 24 + "." + "c" * 24
        diagnostic = staging.redact_diagnostic(f"failed Bearer {token}".encode())
        self.assertNotIn(token, diagnostic)
        self.assertIn("<redacted>", diagnostic)

    def test_policy_is_closed_to_current_pc_scope(self) -> None:
        policy = json.loads(
            (ROOT / "protocol/mcp/p15-inspector-staging-policy-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(policy["tool_count"], 18)
        self.assertEqual(policy["runtime"]["bind"], "127.0.0.1")
        self.assertEqual(policy["runtime"]["scheme"], "https")
        self.assertEqual(
            policy["runtime"]["driver_lifecycle"], "persistent_per_server_run"
        )
        self.assertEqual(policy["runtime"]["shutdown"], "graceful_stdin_eof")
        self.assertFalse(policy["evidence"]["bearer_persisted"])
        self.assertFalse(policy["evidence"]["private_key_persisted"])
        self.assertIn("hancom_2022_runtime", policy["out_of_scope"])
        self.assertIn("hancom_2024_runtime", policy["out_of_scope"])


if __name__ == "__main__":
    unittest.main()
