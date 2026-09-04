from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
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


builder = load_module("p15_quota_builder", "tools/p15/build_quota_contract.py")
validator = load_module("p15_quota_validator", "tools/p15/validate_quota_contract.py")


class QuotaContractTests(unittest.TestCase):
    def test_generated_contract_is_current(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/p15/build_quota_contract.py", "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_passes_repository(self) -> None:
        self.assertEqual(validator.validate(ROOT), [])

    def test_contract_has_exact_closed_shape(self) -> None:
        contract = json.loads(
            (ROOT / "implementation/p15/p15-quota-contract-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(set(contract), validator.EXPECTED_KEYS)
        self.assertEqual(contract["required_behaviors"], validator.EXPECTED_BEHAVIORS)
        self.assertEqual(contract["stages"], validator.EXPECTED_STAGES)
        self.assertEqual(contract["runtime_error_codes"], validator.EXPECTED_ERROR_CODES)
        self.assertEqual(contract["rust_quota_tests"], 8)
        self.assertEqual(contract["rust_regression_tests"], 45)

    def test_policy_dimensions_job_classes_and_limits_are_exact(self) -> None:
        policy = json.loads(
            (ROOT / "protocol/mcp/p15-quota-policy-v1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(policy, validator.EXPECTED_POLICY)
        self.assertEqual(set(policy["buckets"]), {"tenant", "user", "capability"})
        tools = [
            tool
            for job_class in policy["job_classes"]
            for tool in job_class["tools"]
        ]
        self.assertEqual(len(tools), 6)
        self.assertEqual(len(tools), len(set(tools)))

    def test_error_catalog_v2_is_additive_and_schema_valid(self) -> None:
        old = json.loads(
            (ROOT / "protocol/mcp/p15-public-error-catalog-v1.json").read_text(
                encoding="utf-8"
            )
        )
        current = json.loads(
            (ROOT / "protocol/mcp/p15-public-error-catalog-v2.json").read_text(
                encoding="utf-8"
            )
        )
        schema = json.loads(
            (ROOT / "specs/error-envelope.schema.json").read_text(encoding="utf-8")
        )
        schema_validator = Draft202012Validator(schema)
        old_codes = {entry["error_code"] for entry in old["errors"]}
        current_codes = [entry["error_code"] for entry in current["errors"]]
        self.assertEqual(current_codes, validator.EXPECTED_ERROR_CODES)
        self.assertEqual(set(current_codes) - old_codes, {"QUOTA_EXCEEDED", "QUOTA_UNAVAILABLE"})
        for entry in current["errors"]:
            envelope = {
                "schema_version": "hwpx-agent.error/v2",
                "request_id": "req_quota001",
                "error_code": entry["error_code"],
                "category": entry["category"],
                "safe_message": entry["safe_message"],
                "retryable": entry["retryable"],
                "stage": entry["allowed_stages"][0],
                "details": {},
                "recovery": [{"action": entry["recovery_action"]}],
            }
            self.assertEqual(list(schema_validator.iter_errors(envelope)), [])

    def test_policy_or_source_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary)
            required = set(builder.SOURCE_PATHS)
            required.add("implementation/p15/p15-quota-contract-v1.json")
            for relative in required:
                target = clone / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            policy_path = clone / "protocol/mcp/p15-quota-policy-v1.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["buckets"]["tenant"]["capacity"] = 121
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            built = builder.canonical_bytes(builder.build_contract(clone))
            actual = (clone / "implementation/p15/p15-quota-contract-v1.json").read_bytes()
            self.assertNotEqual(built, actual)
            errors = validator.validate(clone)
            self.assertTrue(
                "policy.content" in errors
                or "contract.policy_digest" in errors
                or any(error.endswith(".digest") for error in errors),
                errors,
            )

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


if __name__ == "__main__":
    unittest.main()
