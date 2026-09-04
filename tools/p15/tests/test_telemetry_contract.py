from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, relative: str):
    specification = importlib.util.spec_from_file_location(name, ROOT / relative)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


builder = load_module("p15_telemetry_builder", "tools/p15/build_telemetry_contract.py")
validator = load_module(
    "p15_telemetry_validator", "tools/p15/validate_telemetry_contract.py"
)


class TelemetryContractTests(unittest.TestCase):
    def test_generated_contract_is_current(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/p15/build_telemetry_contract.py", "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_passes_repository(self) -> None:
        self.assertEqual(validator.validate(ROOT), [])

    def test_contract_has_exact_closed_shape_and_predecessor_anchor(self) -> None:
        contract = json.loads(
            (ROOT / "implementation/p15/p15-telemetry-contract-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(set(contract), validator.EXPECTED_KEYS)
        self.assertEqual(contract["required_behaviors"], validator.EXPECTED_BEHAVIORS)
        self.assertEqual(contract["trace_stages"], validator.EXPECTED_STAGES)
        self.assertEqual(
            contract["correlation_fields"], validator.EXPECTED_CORRELATION_FIELDS
        )
        self.assertEqual(contract["p15_07_audited_source_commit"], validator.P15_07_REVISION)
        self.assertEqual(contract["p15_07_contract_sha256"], validator.P15_07_CONTRACT_SHA256)
        self.assertEqual(contract["rust_telemetry_tests"], 8)
        self.assertEqual(contract["rust_regression_tests"], 53)

    def test_policy_hierarchy_dimensions_and_limits_are_exact(self) -> None:
        policy = json.loads(
            (ROOT / "protocol/mcp/p15-telemetry-policy-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(policy, validator.EXPECTED_POLICY)
        self.assertEqual(len(policy["trace_stages"]), len(set(policy["trace_stages"])))
        self.assertEqual(
            len(policy["correlation_fields"]), len(set(policy["correlation_fields"]))
        )
        self.assertEqual(policy["trace_capacity"], 2_048)
        self.assertEqual(policy["max_capability_routes_per_trace"], 128)

    def test_source_sets_are_ordered_duplicate_free_and_equal(self) -> None:
        self.assertEqual(builder.SOURCE_PATHS, validator.EXPECTED_SOURCE_PATHS)
        self.assertEqual(len(builder.SOURCE_PATHS), len(set(builder.SOURCE_PATHS)))

    def test_source_hashes_are_checkout_line_ending_independent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lf = root / "lf.txt"
            crlf = root / "crlf.txt"
            lf.write_bytes(b"first\nsecond\n")
            crlf.write_bytes(b"first\r\nsecond\r\n")
            self.assertEqual(builder.sha256_file(lf), builder.sha256_file(crlf))
            self.assertEqual(validator.sha256(lf), validator.sha256(crlf))
            self.assertEqual(builder.sha256_file(lf), validator.sha256(crlf))

    def test_policy_or_source_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary)
            required = set(builder.SOURCE_PATHS)
            required.add("implementation/p15/p15-telemetry-contract-v1.json")
            for relative in required:
                target = clone / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            policy_path = clone / "protocol/mcp/p15-telemetry-policy-v1.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["trace_capacity"] = 2_049
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            expected = builder.canonical_bytes(builder.build_contract(clone))
            actual = (
                clone / "implementation/p15/p15-telemetry-contract-v1.json"
            ).read_bytes()
            self.assertNotEqual(expected, actual)
            errors = validator.validate(clone)
            self.assertTrue(
                "policy.content" in errors
                or "contract.policy_digest" in errors
                or any(error.endswith(".digest") for error in errors),
                errors,
            )

    def test_source_enforces_privacy_complete_trace_and_single_dispatch(self) -> None:
        telemetry = (ROOT / "crates/mcp-control-plane/src/telemetry.rs").read_text(
            encoding="utf-8"
        )
        handler = (ROOT / "crates/mcp-control-plane/src/handler.rs").read_text(
            encoding="utf-8"
        )
        rust_tests = (ROOT / "crates/mcp-control-plane/tests/telemetry.rs").read_text(
            encoding="utf-8"
        )
        self.assertEqual(handler.count("self.gateway.dispatch(call)"), 1)
        self.assertEqual(rust_tests.count("#[test]"), 8)
        for stage in validator.EXPECTED_STAGES:
            self.assertIn(stage, telemetry)
        for forbidden in [
            "authorization_header",
            "arguments_json",
            "project_id",
            "TenantId",
            "SubjectDigest",
            "signed_url",
            "document_body",
            "raw_xml",
            "renderer",
        ]:
            self.assertNotIn(forbidden, telemetry)
        self.assertNotIn('"hwpx/traceId"', handler)


if __name__ == "__main__":
    unittest.main()
