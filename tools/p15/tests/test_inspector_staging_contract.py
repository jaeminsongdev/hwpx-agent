from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
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
    "p15_inspector_staging_builder", "tools/p15/build_inspector_staging_contract.py"
)
validator = load_module(
    "p15_inspector_staging_validator",
    "tools/p15/validate_inspector_staging_contract.py",
)


class InspectorStagingContractTests(unittest.TestCase):
    def test_historical_contract_is_superseded_only_by_valid_p16_04(self) -> None:
        historical = json.loads(builder.CONTRACT_PATH.read_text(encoding="utf-8"))
        current = builder.build_contract(ROOT)
        historical_locks = {
            item["path"]: item["sha256"] for item in historical["source_locks"]
        }
        current_locks = {
            item["path"]: item["sha256"] for item in current["source_locks"]
        }
        drifted = {
            path
            for path, digest in current_locks.items()
            if historical_locks.get(path) != digest
        }
        self.assertEqual(validator.P16_04_SUPERSEDED_PATHS, drifted)
        self.assertEqual([], validator.validate_p16_04_supersession(ROOT))
        for path in drifted:
            self.assertTrue(
                validator.historical_p15_09_source_matches(
                    ROOT, path, historical_locks[path]
                )
            )

    def test_validator_passes_repository(self) -> None:
        self.assertEqual(validator.validate(ROOT), [])

    def test_contract_is_closed_and_anchored_to_p15_08(self) -> None:
        contract = json.loads(builder.CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(set(contract), validator.EXPECTED_KEYS)
        self.assertEqual(contract["required_behaviors"], validator.EXPECTED_BEHAVIORS)
        self.assertEqual(contract["p15_08_audited_source_commit"], validator.P15_08_REVISION)
        self.assertEqual(contract["p15_08_contract_sha256"], validator.P15_08_CONTRACT_SHA256)
        self.assertTrue(contract["manual_exact_commit_evidence_required"])
        self.assertFalse(contract["production_deployment_qualified"])

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

    def test_policy_or_source_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary)
            required = set(builder.SOURCE_PATHS)
            required.add("implementation/p15/p15-inspector-staging-contract-v1.json")
            for relative in required:
                target = clone / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            policy_path = clone / "protocol/mcp/p15-inspector-staging-policy-v1.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["runtime"]["bind"] = "0.0.0.0"
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            self.assertNotEqual(
                builder.canonical_bytes(builder.build_contract(clone)),
                (clone / "implementation/p15/p15-inspector-staging-contract-v1.json").read_bytes(),
            )
            errors = validator.validate(clone)
            self.assertTrue(
                "policy.runtime" in errors
                or "contract.transport" in errors
                or any(error.endswith(".digest") for error in errors),
                errors,
            )


if __name__ == "__main__":
    unittest.main()
