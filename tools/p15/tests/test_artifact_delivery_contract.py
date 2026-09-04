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


builder = load_module(
    "p15_artifact_delivery_builder", "tools/p15/build_artifact_delivery_contract.py"
)
validator = load_module(
    "p15_artifact_delivery_validator", "tools/p15/validate_artifact_delivery_contract.py"
)


class ArtifactDeliveryContractTests(unittest.TestCase):
    def test_generated_contract_is_current(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/p15/build_artifact_delivery_contract.py", "--check"],
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
            (
                ROOT / "implementation/p15/p15-artifact-delivery-contract-v1.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(set(contract), validator.EXPECTED_KEYS)
        self.assertEqual(contract["required_behaviors"], validator.EXPECTED_BEHAVIORS)
        self.assertEqual(contract["rust_artifact_delivery_tests"], 13)
        self.assertEqual(contract["limits"]["max_ttl_seconds"], 900)
        self.assertEqual(contract["limits"]["max_range_bytes"], 67_108_864)

    def test_catalog_and_public_artifact_schema_remain_frozen(self) -> None:
        contract = builder.build_contract(ROOT)
        self.assertEqual(
            contract["catalog_sha256"],
            "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001",
        )
        catalog = json.loads(
            (ROOT / "protocol/mcp/p15-public-tools-v1.json").read_text(encoding="utf-8")
        )
        artifact = next(tool for tool in catalog["tools"] if tool["name"] == "artifact_get")
        self.assertNotIn("signed_url", json.dumps(artifact["outputSchema"]).lower())
        self.assertEqual(
            artifact["outputSchema"]["properties"]["delivery"]["enum"],
            ["metadata", "preview_in_meta", "attachment_in_content"],
        )

    def test_source_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary)
            contract = json.loads(
                (
                    ROOT / "implementation/p15/p15-artifact-delivery-contract-v1.json"
                ).read_text(encoding="utf-8")
            )
            required = {
                "implementation/p15/p15-artifact-delivery-contract-v1.json",
                "protocol/mcp/p15-public-tools-v1.json",
                "crates/mcp-control-plane/src/artifact_delivery.rs",
                "crates/mcp-control-plane/src/handler.rs",
                "crates/mcp-control-plane/tests/artifact_delivery.rs",
            }
            required.update(entry["path"] for entry in contract["source_locks"])
            for relative in required:
                target = clone / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            with (clone / "crates/mcp-control-plane/src/artifact_delivery.rs").open(
                "a", encoding="utf-8"
            ) as stream:
                stream.write("\n// drift\n")
            errors = validator.validate(clone)
            self.assertTrue(
                any(error.startswith("source_lock[29].digest") for error in errors),
                errors,
            )

    def test_previous_async_contract_is_not_rewritten(self) -> None:
        self.assertEqual(
            validator.sha256(
                ROOT / "implementation/p15/p15-async-job-contract-v1.json"
            ),
            "311e9272373da0129693ad87c8a42e1e6c56b17b34ccb1312eed630b7f049c32",
        )

    def test_source_set_is_ordered_and_duplicate_free(self) -> None:
        self.assertEqual(builder.SOURCE_PATHS, validator.EXPECTED_SOURCE_PATHS)
        self.assertEqual(len(builder.SOURCE_PATHS), len(set(builder.SOURCE_PATHS)))


if __name__ == "__main__":
    unittest.main()
