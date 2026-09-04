from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools" / "p14" / "validate_metadata_migrations.py"
SPEC = importlib.util.spec_from_file_location("validate_metadata_migrations", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CONTRACT_PATH = (
    ROOT / "implementation" / "p14" / "postgres" / "p14-metadata-v1.json"
)


class MetadataMigrationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = MODULE.load_json(CONTRACT_PATH)

    def test_canonical_contract_is_valid(self) -> None:
        validated = MODULE.validate_contract(CONTRACT_PATH, ROOT)
        self.assertEqual(validated["table_count"], 13)
        self.assertEqual(validated["tenant_scoped_table_count"], 12)

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"schema_version":"a","schema_version":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                MODULE.load_json(path)

    def test_unknown_contract_property_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["fallback_database"] = "sqlite"
        with self.assertRaisesRegex(ValueError, "contract keys differ"):
            self._validate_document(contract)

    def test_unpinned_container_image_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["database"]["container_image"] = "postgres:18.4-bookworm"
        with self.assertRaisesRegex(ValueError, "not pinned"):
            self._validate_document(contract)

    def test_different_pinned_container_digest_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["database"]["container_image"] = "postgres:18.4-bookworm@sha256:" + "f" * 64
        with self.assertRaisesRegex(ValueError, "digest differs"):
            self._validate_document(contract)

    def test_repository_escape_path_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["migrations"]["up_path"] = "../outside.sql"
        with self.assertRaisesRegex(ValueError, "escapes repository root"):
            self._validate_document(contract)

    def test_tampered_up_migration_digest_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["migrations"]["up_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "up migration digest mismatch"):
            self._validate_document(contract)

    def test_zero_digest_placeholder_in_up_sql_is_rejected(self) -> None:
        replacement = (
            ROOT / "migrations" / "postgres" / "0001_p14_metadata.up.sql"
        ).read_text(encoding="utf-8").replace(
            "current_setting('hwpx_agent.migration_sha256')", "'" + "0" * 64 + "'"
        )
        with self.assertRaisesRegex(ValueError, "zero digest placeholder"):
            self._validate_with_replaced_file("migrations/up.sql", replacement, "up")

    def test_database_extension_in_up_sql_is_rejected(self) -> None:
        original = (
            ROOT / "migrations" / "postgres" / "0001_p14_metadata.up.sql"
        ).read_text(encoding="utf-8")
        replacement = original.replace("CREATE SCHEMA hwpx_agent;", "CREATE EXTENSION pgcrypto;\nCREATE SCHEMA hwpx_agent;")
        with self.assertRaisesRegex(ValueError, "must not require database extensions"):
            self._validate_with_replaced_file("migrations/up.sql", replacement, "up")

    def test_missing_tenant_rls_table_is_rejected(self) -> None:
        original = (
            ROOT / "migrations" / "postgres" / "0001_p14_metadata.up.sql"
        ).read_text(encoding="utf-8")
        replacement = original.replace("'tenants', 'projects', 'branches',", "'tenants', 'projects',")
        with self.assertRaisesRegex(ValueError, "tenant RLS table sequence differs"):
            self._validate_with_replaced_file("migrations/up.sql", replacement, "up")

    def test_down_migration_without_explicit_gate_is_rejected(self) -> None:
        original = (
            ROOT / "migrations" / "postgres" / "0001_p14_metadata.down.sql"
        ).read_text(encoding="utf-8")
        replacement = original.replace(
            "current_setting('hwpx_agent.allow_destructive_rollback', true)",
            "'on'",
        )
        with self.assertRaisesRegex(ValueError, "down migration is missing required SQL"):
            self._validate_with_replaced_file("migrations/down.sql", replacement, "down")

    def test_smoke_assertion_count_drift_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["smoke_fixture"]["assertions_per_run"] = 18
        with self.assertRaisesRegex(ValueError, "smoke assertion count differs"):
            self._validate_document(contract)

    def test_source_lock_drift_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["source_locks"][0]["sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "source lock 0 digest mismatch"):
            self._validate_document(contract)

    def _validate_document(self, contract: dict[str, object]) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            MODULE.validate_contract(path, ROOT)

    def _validate_with_replaced_file(self, relative: str, content: str, kind: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            for key in ("up", "down"):
                source = ROOT / "migrations" / "postgres" / f"0001_p14_metadata.{key}.sql"
                destination = temporary_root / "migrations" / f"{key}.sql"
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read_bytes())
            fixture_source = ROOT / "tools" / "p14" / "fixtures" / "p14_metadata_smoke.sql"
            fixture_destination = temporary_root / "tools" / "p14" / "fixtures" / fixture_source.name
            fixture_destination.parent.mkdir(parents=True, exist_ok=True)
            fixture_destination.write_bytes(fixture_source.read_bytes())
            for source_lock in self.contract["source_locks"]:
                source = ROOT / source_lock["path"]
                destination = temporary_root / source_lock["path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read_bytes())

            replacement_path = temporary_root / relative
            replacement_path.parent.mkdir(parents=True, exist_ok=True)
            replacement_path.write_text(content, encoding="utf-8", newline="\n")
            contract = copy.deepcopy(self.contract)
            contract["migrations"][f"{kind}_path"] = relative
            contract["migrations"][f"{kind}_sha256"] = hashlib.sha256(
                replacement_path.read_bytes()
            ).hexdigest()
            contract["migrations"][f"{'down' if kind == 'up' else 'up'}_path"] = (
                f"migrations/{'down' if kind == 'up' else 'up'}.sql"
            )
            contract["smoke_fixture"]["path"] = (
                "tools/p14/fixtures/p14_metadata_smoke.sql"
            )
            contract_path = temporary_root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            MODULE.validate_contract(contract_path, temporary_root)


if __name__ == "__main__":
    unittest.main()
