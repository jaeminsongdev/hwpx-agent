from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[3]
P15_TOOLS = ROOT / "tools/p15"
sys.path.insert(0, str(P15_TOOLS))

import build_public_tool_schemas as builder  # noqa: E402
import validate_public_tool_schemas as validator  # noqa: E402


class PublicToolSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = validator.load_json(builder.CATALOG_PATH)
        cls.snapshot = validator.load_json(builder.SNAPSHOT_PATH)
        cls.contract = validator.load_json(builder.CONTRACT_PATH)
        cls.auth_contract = validator.load_json(validator.AUTH_CONTRACT_PATH)

    def tool(self, name: str) -> dict:
        return next(tool for tool in self.catalog["tools"] if tool["name"] == name)

    def test_current_contract_passes(self) -> None:
        self.assertEqual(
            validator.validate_all(
                self.catalog,
                self.snapshot,
                self.contract,
                self.auth_contract,
                ROOT,
            ),
            [],
        )

    def test_exact_eighteen_tool_names_are_frozen(self) -> None:
        self.assertEqual(self.catalog["descriptor_count"], 18)
        self.assertEqual(
            [tool["name"] for tool in self.catalog["tools"]], builder.TOOL_ORDER
        )

    def test_every_input_and_output_schema_accepts_a_bounded_fixture(self) -> None:
        for tool in self.catalog["tools"]:
            for key in ("inputSchema", "outputSchema"):
                schema = tool[key]
                fixture = validator.synthesize(schema, schema)
                self.assertEqual(
                    list(Draft202012Validator(schema).iter_errors(fixture)),
                    [],
                    f"{tool['name']}:{key}",
                )

    def test_every_schema_rejects_an_unknown_root_property(self) -> None:
        for tool in self.catalog["tools"]:
            for key in ("inputSchema", "outputSchema"):
                schema = tool[key]
                fixture = validator.synthesize(schema, schema)
                fixture["unexpected_property"] = True
                self.assertFalse(
                    Draft202012Validator(schema).is_valid(fixture),
                    f"{tool['name']}:{key}",
                )

    def test_hancom_2022_profile_is_not_predeclared_on_this_pc(self) -> None:
        schema = self.tool("capability_check")["inputSchema"]
        fixture = validator.synthesize(schema, schema)
        fixture["target_profile"] = "hancom-2022-12.0.0-ko-KR"
        self.assertFalse(Draft202012Validator(schema).is_valid(fixture))

    def test_project_create_requires_current_target_and_null_revision(self) -> None:
        schema = self.tool("project_create")["inputSchema"]
        fixture = validator.synthesize(schema, schema)
        self.assertEqual(fixture["target_profile"], "hancom-hangul-2020-secondary")
        self.assertIsNone(fixture["expected_revision"])
        fixture["expected_revision"] = "rev_existing01"
        self.assertFalse(Draft202012Validator(schema).is_valid(fixture))

    def test_security_mirror_drift_is_rejected(self) -> None:
        catalog = deepcopy(self.catalog)
        catalog["tools"][0]["_meta"]["securitySchemes"][0]["scopes"] = []
        errors = validator.validate_catalog(catalog, self.auth_contract)
        self.assertIn("capability_check.security_mirror", errors)

    def test_unregistered_scope_is_rejected(self) -> None:
        catalog = deepcopy(self.catalog)
        catalog["tools"][0]["securitySchemes"][0]["scopes"] = ["admin.everything"]
        catalog["tools"][0]["_meta"]["securitySchemes"][0]["scopes"] = [
            "admin.everything"
        ]
        errors = validator.validate_catalog(catalog, self.auth_contract)
        self.assertIn("capability_check.security", errors)
        self.assertIn("capability_check.unknown_auth_scope", errors)

    def test_annotation_weakening_is_rejected(self) -> None:
        catalog = deepcopy(self.catalog)
        cancel = next(tool for tool in catalog["tools"] if tool["name"] == "job_cancel")
        cancel["annotations"]["destructiveHint"] = False
        self.assertIn(
            "job_cancel.annotations",
            validator.validate_catalog(catalog, self.auth_contract),
        )

    def test_only_job_cancel_is_destructive(self) -> None:
        destructive = [
            tool["name"]
            for tool in self.catalog["tools"]
            if tool["annotations"]["destructiveHint"]
        ]
        self.assertEqual(destructive, ["job_cancel"])

    def test_read_only_set_is_exact(self) -> None:
        observed = {
            tool["name"]
            for tool in self.catalog["tools"]
            if tool["annotations"]["readOnlyHint"]
        }
        self.assertEqual(observed, builder.READ_ONLY)

    def test_state_creating_tools_require_idempotency(self) -> None:
        for tool in self.catalog["tools"]:
            required = tool["inputSchema"]["required"]
            if tool["name"] in builder.READ_ONLY:
                self.assertNotIn("idempotency_key", required, tool["name"])
            else:
                self.assertIn("idempotency_key", required, tool["name"])

    def test_revision_mutations_require_expected_revision(self) -> None:
        for name in builder.REVISION_MUTATIONS:
            self.assertIn("expected_revision", self.tool(name)["inputSchema"]["required"])

    def test_forbidden_secret_field_is_rejected(self) -> None:
        catalog = deepcopy(self.catalog)
        target = catalog["tools"][0]["outputSchema"]
        target["properties"]["password"] = {"type": "string", "maxLength": 10}
        errors = validator.validate_catalog(catalog, self.auth_contract)
        self.assertTrue(
            any(error.startswith("capability_check.output.forbidden_properties") for error in errors)
        )

    def test_snapshot_hash_drift_is_rejected(self) -> None:
        snapshot = deepcopy(self.snapshot)
        snapshot["entries"][0]["input_schema_sha256"] = "0" * 64
        self.assertEqual(validator.validate_snapshot(snapshot, self.catalog), ["snapshot.drift"])

    def test_source_hash_drift_is_rejected(self) -> None:
        contract = deepcopy(self.contract)
        contract["source_locks"][0]["sha256"] = "0" * 64
        self.assertIn(
            "contract.source_locks[0].drift",
            validator.validate_source_locks(contract, ROOT),
        )

    def test_generated_files_are_deterministic(self) -> None:
        self.assertEqual(builder.check_all(ROOT), [])


if __name__ == "__main__":
    unittest.main()
