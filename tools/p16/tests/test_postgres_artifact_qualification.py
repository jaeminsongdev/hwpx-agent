from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/p16/postgres_artifact_qualification.py"
SPEC = importlib.util.spec_from_file_location("postgres_artifact_qualification", SOURCE)
assert SPEC is not None and SPEC.loader is not None
qualification = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualification)


class PostgresArtifactQualificationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="hwpx-p16-qualification-test-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        paths = set(qualification.RUNTIME_PATHS) | set(qualification.GUARD_PATHS) | {
            qualification.PREDECESSOR_PATH, qualification.CONTRACT_PATH,
            f"{qualification.BASE}/current-db.json", f"{qualification.BASE}/independent-db.json",
        }
        for relative in paths:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        self.receipt = json.loads((self.root / f"{qualification.BASE}/current-db.json").read_bytes())

    def write_contract(self, value):
        (self.root / qualification.CONTRACT_PATH).write_text(json.dumps(value), encoding="utf-8")

    def test_exact_successor_admits_only_the_three_declared_p14_sources(self):
        replacements = qualification.verified_replacements(self.root)
        self.assertEqual(tuple(replacements), qualification.REPLACED_PATHS)
        self.assertNotIn("Cargo.lock", replacements)
        self.assertNotIn("crates/artifact-service/src/crypto.rs", replacements)
        self.assertTrue(all(before != after for before, after in replacements.values()))

    def test_current_runtime_source_drift_is_not_an_automatic_new_qualification(self):
        target = self.root / "crates/artifact-service/src/store/postgres_repository.rs"
        target.write_bytes(target.read_bytes() + b"\n// changed runtime\n")
        with self.assertRaisesRegex(qualification.QualificationError, "source.runtime_digest"):
            qualification.verified_replacements(self.root)

    def test_guard_source_change_is_rejected(self):
        target = self.root / qualification.GUARD_PATHS[0]
        target.write_bytes(target.read_bytes() + b"\n# changed validator\n")
        with self.assertRaisesRegex(qualification.QualificationError, "contract.exact"):
            qualification.verified_replacements(self.root)

    def test_predecessor_contract_cannot_be_rewritten(self):
        target = self.root / qualification.PREDECESSOR_PATH
        target.write_bytes(target.read_bytes() + b" ")
        with self.assertRaisesRegex(qualification.QualificationError, "predecessor.digest"):
            qualification.verified_replacements(self.root)

    def test_missing_or_changed_independent_receipt_is_rejected(self):
        target = self.root / f"{qualification.BASE}/independent-db.json"
        original = target.read_bytes()
        target.write_bytes(original + b" ")
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.digest"):
            qualification.verified_replacements(self.root)
        target.unlink()
        with self.assertRaisesRegex(qualification.QualificationError, "qualification.unavailable"):
            qualification.verified_replacements(self.root)

    def test_more_source_paths_or_promoted_claims_are_rejected(self):
        baseline = qualification.expected_contract(self.root)
        for mutate in (
            lambda value: value["claims"].update(phase_complete=True),
            lambda value: value["claims"].update(actual_hangul=0),
            lambda value: value["replacements"].append(value["replacements"][0]),
            lambda value: value.update(allow_any_source=True),
            lambda value: value.update(audited_source_commit="0" * 40),
        ):
            changed = copy.deepcopy(baseline)
            mutate(changed)
            self.write_contract(changed)
            with self.assertRaisesRegex(qualification.QualificationError, "contract.exact"):
                qualification.verified_replacements(self.root)

    def test_receipt_failure_cleanup_or_scope_drift_is_rejected_semantically(self):
        for key, value in (
            ("decision", "FAIL"), ("owned_resources_removed", False), ("owned_resources_removed", 1),
            ("actual_hangul", 0), ("registered_host", True), ("failure", "private-sentinel"),
            ("failed_stage", "seed"), ("run_id", "f" * 32), ("image", "postgres:latest"),
        ):
            changed = copy.deepcopy(self.receipt)
            changed[key] = value
            with self.subTest(key=key, value=value), self.assertRaisesRegex(qualification.QualificationError, "receipt.state"):
                qualification.validate_receipt(changed, self.receipt["run_id"])

    def test_receipt_missing_explicit_null_or_unknown_field_is_rejected(self):
        for key in ("failure", "failed_stage"):
            changed = copy.deepcopy(self.receipt)
            del changed[key]
            with self.assertRaisesRegex(qualification.QualificationError, "receipt.keys"):
                qualification.validate_receipt(changed, self.receipt["run_id"])
        changed = copy.deepcopy(self.receipt)
        changed["raw_sql"] = "private-sentinel"
        with self.assertRaisesRegex(qualification.QualificationError, "receipt.keys"):
            qualification.validate_receipt(changed, self.receipt["run_id"])

    def test_receipt_check_sequence_cannot_omit_reorder_duplicate_or_invent_proof(self):
        baseline = self.receipt["checks"]
        for checks in (baseline[1:], list(reversed(baseline)), baseline + [baseline[-1]],
                       ["PASS"], [], [True], ["restart_ephemeral_port_reassigned"] + baseline):
            changed = copy.deepcopy(self.receipt)
            changed["checks"] = checks
            with self.subTest(checks=checks), self.assertRaisesRegex(qualification.QualificationError, "receipt.checks"):
                qualification.validate_receipt(changed, self.receipt["run_id"])

    def test_unchanged_port_observation_does_not_skip_restart_verification(self):
        changed = copy.deepcopy(self.receipt)
        changed["checks"].remove("restart_ephemeral_port_reassigned")
        self.assertEqual(qualification.validate_receipt(changed, self.receipt["run_id"]), self.receipt["source_sha256"])

    def test_receipt_source_and_binary_hashes_are_exactly_bounded(self):
        for field in ("source_sha256", "probe_sha256"):
            changed = copy.deepcopy(self.receipt)
            changed[field] = {}
            with self.assertRaises(qualification.QualificationError):
                qualification.validate_receipt(changed, self.receipt["run_id"])
        for value in (True, "f" * 63, "F" * 64, "f" * 65):
            changed = copy.deepcopy(self.receipt)
            changed["source_sha256"]["Cargo.lock"] = value
            with self.assertRaisesRegex(qualification.QualificationError, "receipt.source_digest"):
                qualification.validate_receipt(changed, self.receipt["run_id"])

    def test_json_duplicates_nonfinite_numbers_and_recursion_fail_closed(self):
        for raw in (b'{"decision":"PASS","dec\\u0069sion":"FAIL"}', b'{"a":NaN}',
                    b'{"a":Infinity}', b'\xff', b'[' * 2000 + b']' * 2000):
            with self.subTest(raw=raw[:30]), self.assertRaises(qualification.QualificationError):
                qualification.json_value(raw)

    def test_source_paths_and_read_limits_fail_closed(self):
        for relative in ("../outside", "/outside", "C:/outside", "a\\b", "a//b", "a/./b", "a/../b", ""):
            with self.subTest(relative=relative), self.assertRaises(qualification.QualificationError):
                qualification.read_bounded(self.root, relative)
        with self.assertRaisesRegex(qualification.QualificationError, "file.bound"):
            qualification.read_bounded(self.root, qualification.CONTRACT_PATH, 1)
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaisesRegex(qualification.QualificationError, "path.link"):
                qualification.read_bounded(self.root, qualification.CONTRACT_PATH)

    def test_depth_budget_ignores_json_string_punctuation_and_escaped_quotes(self):
        value = {"quoted": '[{\\"' * 1000}
        self.assertEqual(qualification.json_value(json.dumps(value).encode("utf-8")), value)
        qualification.json_value(b"[" * 32 + b"]" * 32)
        with self.assertRaisesRegex(qualification.QualificationError, "json.depth"):
            qualification.json_value(b"[" * 33 + b"]" * 33)

    def test_writer_never_overwrites_a_qualification(self):
        target = self.root / qualification.CONTRACT_PATH
        original = target.read_bytes()
        output = io.StringIO()
        with patch.object(qualification, "ROOT", self.root), patch("sys.argv", ["qualification", "--write"]):
            with contextlib.redirect_stdout(output):
                self.assertEqual(qualification.main(), 1)
        self.assertEqual(target.read_bytes(), original)
        self.assertNotIn(str(self.root), output.getvalue())


if __name__ == "__main__":
    unittest.main()
