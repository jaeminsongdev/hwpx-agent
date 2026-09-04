from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools" / "p14" / "validate_artifact_service_migration.py"
SPEC = importlib.util.spec_from_file_location("validate_artifact_service_migration", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CONTRACT_PATH = (
    ROOT / "implementation" / "p14" / "postgres" / "p14-artifact-service-v1.json"
)


class ArtifactServiceMigrationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = MODULE.load_json(CONTRACT_PATH)

    def test_canonical_contract_is_valid(self) -> None:
        validated = MODULE.validate_contract(CONTRACT_PATH, ROOT)
        self.assertEqual(validated["artifact_column_count"], 14)
        self.assertEqual(validated["smoke_assertions_per_run"], 22)

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"contract_id":"a","contract_id":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                MODULE.load_json(path)

    def test_unknown_contract_property_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["fallback_store"] = "plaintext"
        with self.assertRaisesRegex(ValueError, "contract keys differ"):
            self._validate_document(contract)

    def test_unpinned_or_different_image_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["database"]["container_image"] = "postgres:18.4-bookworm"
        with self.assertRaisesRegex(ValueError, "exact approved digest"):
            self._validate_document(contract)

    def test_repository_escape_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["migration"]["up_path"] = "../outside.sql"
        with self.assertRaisesRegex(ValueError, "escapes repository root"):
            self._validate_document(contract)

    def test_tampered_up_digest_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["migration"]["up_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "up migration digest mismatch"):
            self._validate_document(contract)

    def test_zero_digest_placeholder_is_rejected(self) -> None:
        original = (ROOT / self.contract["migration"]["up_path"]).read_text(encoding="utf-8")
        replacement = original.replace(
            "current_setting('hwpx_agent.migration_sha256')", "'" + "0" * 64 + "'"
        )
        with self.assertRaisesRegex(ValueError, "zero digest placeholder"):
            self._validate_with_replacement("migration", "up", replacement)

    def test_forced_rls_removal_is_rejected(self) -> None:
        original = (ROOT / self.contract["migration"]["up_path"]).read_text(encoding="utf-8")
        replacement = original.replace(
            "ALTER TABLE hwpx_agent.artifact_acl FORCE ROW LEVEL SECURITY;", ""
        )
        with self.assertRaisesRegex(ValueError, "FORCE ROW LEVEL SECURITY"):
            self._validate_with_replacement("migration", "up", replacement)

    def test_final_manager_guard_removal_is_rejected(self) -> None:
        original = (ROOT / self.contract["migration"]["up_path"]).read_text(encoding="utf-8")
        replacement = original.replace(
            "artifact ACL must retain at least one manager", "manager guard removed"
        )
        with self.assertRaisesRegex(ValueError, "retain at least one manager"):
            self._validate_with_replacement("migration", "up", replacement)

    def test_version_one_schema_drop_is_rejected(self) -> None:
        original = (ROOT / self.contract["migration"]["down_path"]).read_text(encoding="utf-8")
        replacement = original.replace("BEGIN;", "BEGIN;\nDROP SCHEMA hwpx_agent CASCADE;")
        with self.assertRaisesRegex(ValueError, "must preserve the version 1 schema"):
            self._validate_with_replacement("migration", "down", replacement)

    def test_smoke_assertion_count_drift_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["smoke_fixture"]["assertions_per_run"] = 19
        with self.assertRaisesRegex(ValueError, "assertion count differs"):
            self._validate_document(contract)

    def test_source_lock_drift_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["source_locks"][3]["sha256"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "source lock 3 digest mismatch"):
            self._validate_document(contract)

    def _validate_document(self, contract: dict[str, object]) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            MODULE.validate_contract(path, ROOT)

    def _validate_with_replacement(self, section: str, kind: str, content: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            contract = copy.deepcopy(self.contract)
            paths: set[str] = set()
            for migration_section in ("prerequisite", "migration"):
                paths.add(contract[migration_section]["up_path"])
                paths.add(contract[migration_section]["down_path"])
            paths.add(contract["smoke_fixture"]["path"])
            paths.update(source["path"] for source in contract["source_locks"])
            for relative in paths:
                source = ROOT / relative
                target = temporary_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())

            replacement_path = temporary_root / contract[section][f"{kind}_path"]
            replacement_path.write_text(content, encoding="utf-8", newline="\n")
            contract[section][f"{kind}_sha256"] = hashlib.sha256(
                replacement_path.read_bytes()
            ).hexdigest()
            contract_path = temporary_root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            MODULE.validate_contract(contract_path, temporary_root)


if __name__ == "__main__":
    unittest.main()
