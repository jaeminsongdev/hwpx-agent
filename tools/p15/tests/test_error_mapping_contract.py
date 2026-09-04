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


builder = load_module("p15_error_builder", "tools/p15/build_error_mapping_contract.py")
validator = load_module(
    "p15_error_validator", "tools/p15/validate_error_mapping_contract.py"
)


class ErrorMappingContractTests(unittest.TestCase):
    def test_generated_contract_is_current(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/p15/build_error_mapping_contract.py", "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_passes_repository(self) -> None:
        self.assertEqual(validator.validate(ROOT), [])

    def test_contract_and_catalog_have_exact_closed_shape(self) -> None:
        contract = json.loads(
            (ROOT / "implementation/p15/p15-error-mapping-contract-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(set(contract), validator.EXPECTED_KEYS)
        self.assertEqual(contract["required_behaviors"], validator.EXPECTED_BEHAVIORS)
        self.assertEqual(contract["stages"], validator.EXPECTED_STAGES)
        self.assertEqual(len(contract["error_codes"]), 14)
        self.assertEqual(contract["error_codes"], sorted(contract["error_codes"]))
        self.assertEqual(contract["rust_error_mapping_tests"], 5)

    def test_every_catalog_entry_builds_a_valid_bounded_envelope(self) -> None:
        catalog = json.loads(
            (ROOT / "protocol/mcp/p15-public-error-catalog-v1.json").read_text(
                encoding="utf-8"
            )
        )
        schema = json.loads(
            (ROOT / "specs/error-envelope.schema.json").read_text(encoding="utf-8")
        )
        envelope_validator = Draft202012Validator(schema)
        for entry in catalog["errors"]:
            envelope = {
                "schema_version": "hwpx-agent.error/v2",
                "request_id": "req_server_0123456789abcdef0123456789abcdef",
                "error_code": entry["error_code"],
                "category": entry["category"],
                "safe_message": entry["safe_message"],
                "retryable": entry["retryable"],
                "stage": entry["allowed_stages"][0],
                "details": {},
                "recovery": [{"action": entry["recovery_action"]}],
            }
            self.assertEqual(list(envelope_validator.iter_errors(envelope)), [])
            envelope["details"] = {"local_path": "D:/private/document.hwpx"}
            self.assertNotEqual(list(envelope_validator.iter_errors(envelope)), [])

    def test_source_or_catalog_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary)
            contract = json.loads(
                (ROOT / "implementation/p15/p15-error-mapping-contract-v1.json").read_text(
                    encoding="utf-8"
                )
            )
            required = {
                "implementation/p15/p15-error-mapping-contract-v1.json",
                "protocol/mcp/p15-public-error-catalog-v1.json",
                "specs/error-envelope.schema.json",
                "protocol/mcp/p15-public-tools-v1.json",
                "implementation/p15/p15-artifact-delivery-contract-v1.json",
                "crates/mcp-control-plane/src/error_catalog.rs",
                "crates/mcp-control-plane/src/handler.rs",
                "crates/mcp-control-plane/tests/error_mapping.rs",
                "crates/mcp-control-plane/tests/handler_contract.rs",
            }
            required.update(entry["path"] for entry in contract["source_locks"])
            for relative in required:
                target = clone / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            (clone / "protocol/mcp/p15-public-error-catalog-v1.json").write_text(
                '{"errors":[],"schema_version":"hwpx-agent.public-error-catalog/v1"}\n',
                encoding="utf-8",
            )
            errors = validator.validate(clone)
            self.assertTrue(
                "contract.error_catalog_sha256" in errors
                or any(error.endswith(".digest") for error in errors),
                errors,
            )

    def test_source_sets_are_ordered_duplicate_free_and_equal(self) -> None:
        self.assertEqual(builder.SOURCE_PATHS, validator.EXPECTED_SOURCE_PATHS)
        self.assertEqual(len(builder.SOURCE_PATHS), len(set(builder.SOURCE_PATHS)))


if __name__ == "__main__":
    unittest.main()
