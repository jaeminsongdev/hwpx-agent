"""Closed build-input contract fixtures; never compiles or creates a target."""
import base64
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import conservative_maintenance as c
import current_issuer_build_inputs as subject


def pin(name, digest="a"*64):
    return {"path": name, "bytes": 1, "sha256": digest}


class Reader:
    def __init__(self, pins=None, documents=None, texts=None):
        self.pins, self.documents, self.texts = pins or {}, documents or {}, texts or {}
        self.calls = []

    def fresh_pin(self, name):
        self.calls.append(name)
        return copy.deepcopy(self.pins[name])

    def json(self, name):
        return copy.deepcopy(self.documents[name])

    def text(self, name):
        return self.texts[name]


class CurrentIssuerBuildInputsTests(unittest.TestCase):
    def baseline(self):
        names = sorted(subject.RUST_CHANGES)+[subject.BUILDER]+[f"crates/fixture_{n}.rs" for n in range(832)]
        old = {name: pin(name) for name in names}
        approved = {name: pin(name, "b"*64) for name in subject.RUST_CHANGES|{subject.BUILDER}}
        actual = dict(old, **approved)
        return old, approved, actual

    def prior_build(self):
        source, _, _ = self.baseline()
        protected = [pin(f"target/protected/fixture_{n}.exe") for n in range(49)]
        return {"state": "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE", "exit_code": 0,
            "source_freeze_exact_after": True, "protected_executables_exact_after": True,
            "whole_workspace_Rust_input_coverage_enforced": True, "historical_parent_archive_verified": True,
            "build_finished_success": True, "diagnostics": [], "catalog_profile": {"test": False},
            "logical_cpu_limit": 1, "cargo_jobs": 1, "priority": "BelowNormal",
            "source_freeze": list(source.values()), "protected_executables": protected,
            "executable_pin": pin(subject.LEGACY+"/debug/examples/formula_issuer_product_postgres_probe-p143-r14.exe")}

    def reviews(self):
        helpers = [pin(name, "b"*64) for name in sorted(subject.RUST_CHANGES)]
        helpers += [pin(f"tools/helper_{n}.py") for n in range(42)]
        audit = {"state": "INPUT_CHANGED_REBUILD_REQUIRED_NOT_SQL_OR_GATE", "source_drift_count": 9,
            "protected_drift_count": 0, "missing_or_link_count": 0, "source_checked": 842,
            "protected_checked": 50, "observed_inputs_fresh_after": True, "helper_freeze_exact_after": True,
            "compiler_build_binding_accepted": False, "public_code_drift_paths": sorted(subject.RUST_CHANGES),
            "helper_freeze": helpers}
        qualified = {"state": "PASS_COMPILER_SUPERVISOR_SOURCE_MOCK_ONLY_NOT_BUILD_SQL_OR_GATE",
            "tests_run": 23, "tests_passed": 23, "failed_tests": [], "source_freeze_exact_after": True,
            "actual_Cargo_Rustc_SQL_Docker_native_child_or_full_audit_run": False,
            "source_freeze": [pin(subject.BUILDER, "b"*64)]+[pin(f"tools/qualified_{n}.py") for n in range(13)]}
        return audit, qualified

    def test_pin_path_shape_value_and_root_escape_are_rejected(self):
        self.assertEqual(subject.pin_shape(pin("crates/valid.rs"))["bytes"], 1)
        for change in ({"path": "../escape"}, {"path": "target/../escape"}, {"path": "C:/escape"},
                {"path": "target\\escape"}, {"path": "/escape"}, {"path": "target//escape"},
                {"bytes": True}, {"bytes": -1}, {"sha256": "not-a-pin"}, {"extra": "forbidden"}):
            row = dict(pin("crates/valid.rs"), **change)
            with self.assertRaises(ValueError):
                subject.pin_shape(row)

    def test_inventory_exact_count_and_uniqueness_are_required(self):
        for rows in ([], [pin("crates/a.rs")], [pin("crates/a.rs"), pin("crates/a.rs")]):
            with self.assertRaises(ValueError):
                subject.inventory(rows, 2)
        self.assertEqual(len(subject.inventory([pin("crates/a.rs"), pin("crates/b.rs")], 2)), 2)

    def test_baseline_full_842_and_49_plus_current_coverage_are_required(self):
        build = self.prior_build()
        source, protected = subject.baseline_contract(build)
        self.assertEqual((len(source), len(protected)), (842, 50))
        for field in ("source_freeze", "protected_executables"):
            changed = copy.deepcopy(build)
            changed[field].pop()
            with self.assertRaises(ValueError):
                subject.baseline_contract(changed)

    def test_baseline_flags_terminal_and_resource_contract_cannot_be_weakened(self):
        build = self.prior_build()
        for field, value in (("exit_code", False), ("exit_code", 1), ("source_freeze_exact_after", False),
                ("protected_executables_exact_after", False), ("whole_workspace_Rust_input_coverage_enforced", False),
                ("historical_parent_archive_verified", False), ("build_finished_success", False),
                ("catalog_profile", {"test": True}), ("diagnostics", [{"level": "warning"}]),
                ("logical_cpu_limit", True), ("cargo_jobs", 2), ("priority", "Normal")):
            changed = copy.deepcopy(build)
            changed[field] = value
            with self.assertRaises(ValueError):
                subject.baseline_contract(changed)

    def test_review_evidence_pins_only_allow_explicit_nine_rust_plus_builder(self):
        audit, qualification = self.reviews()
        approved, helpers = subject.reviewed_deltas(audit, qualification)
        self.assertEqual(set(approved), subject.RUST_CHANGES|{subject.BUILDER})
        self.assertEqual(len(helpers), 14)
        for field, value in (("source_drift_count", 8), ("protected_drift_count", 1),
                ("compiler_build_binding_accepted", True), ("public_code_drift_paths", [])):
            changed = copy.deepcopy(audit)
            changed[field] = value
            with self.assertRaises(ValueError):
                subject.reviewed_deltas(changed, qualification)
        qualification["tests_passed"] = 22
        with self.assertRaises(ValueError):
            subject.reviewed_deltas(audit, qualification)

    def test_fresh_whole_842_reads_bind_current_and_do_not_rewrite_old_pins(self):
        old, approved, actual = self.baseline()
        before = copy.deepcopy(old)
        reader = Reader(actual)
        rows, changed = subject.bind_current_sources(reader, old, approved)
        self.assertEqual(len(rows), 842)
        self.assertEqual(set(changed), set(approved))
        self.assertEqual(len(reader.calls), 842)
        self.assertEqual(old, before)

    def test_unreviewed_source_delta_is_never_silently_added(self):
        old, approved, actual = self.baseline()
        actual["crates/fixture_0.rs"] = pin("crates/fixture_0.rs", "c"*64)
        with self.assertRaisesRegex(ValueError, "CURRENT_ISSUER_UNREVIEWED_SOURCE_DRIFT"):
            subject.bind_current_sources(Reader(actual), old, approved)

    def test_approved_pin_drift_or_missing_declared_change_is_rejected(self):
        for phase in ("pin", "not-changed", "extra"):
            old, approved, actual = self.baseline()
            name = next(iter(subject.RUST_CHANGES))
            if phase == "pin":
                actual[name] = pin(name, "c"*64)
            elif phase == "not-changed":
                approved[name] = actual[name] = old[name]
            else:
                approved["crates/fixture_0.rs"] = old["crates/fixture_0.rs"]
            with self.assertRaises(ValueError):
                subject.bind_current_sources(Reader(actual), old, approved)

    def parent_fixture(self):
        raw = b"pub mod first;\npub mod source_formula_policy;\npub mod last;\n"
        old = {subject.PARENT: {"path": subject.PARENT, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}}
        row = dict(old[subject.PARENT], base64_chunks=[base64.b64encode(raw).decode("ascii")])
        text = raw.decode().replace("pub mod source_formula_policy;\n", "pub mod source_formula_policy;\npub mod schema22;\n")
        return old, Reader(documents={subject.PARENT_ARCHIVE: {"files": [row]}}, texts={subject.PARENT: text})

    def test_historical_parent_preimage_and_single_module_delta_are_exact(self):
        old, reader = self.parent_fixture()
        subject.verify_historical_parent(reader, old)
        original = reader.documents[subject.PARENT_ARCHIVE]["files"][0]
        del original["bytes"]
        del original["sha256"]
        subject.verify_historical_parent(reader, old)
        reader.texts[subject.PARENT] += "pub mod undeclared;\n"
        with self.assertRaisesRegex(ValueError, "CURRENT_ISSUER_PARENT_UNDECLARED_CHANGE"):
            subject.verify_historical_parent(reader, old)

    def test_historical_parent_corrupt_archive_or_insertion_marker_is_rejected(self):
        old, reader = self.parent_fixture()
        reader.documents[subject.PARENT_ARCHIVE]["files"][0]["sha256"] = "f"*64
        with self.assertRaisesRegex(ValueError, "CURRENT_ISSUER_PARENT_PREIMAGE_DRIFT"):
            subject.verify_historical_parent(reader, old)

    def closure_fixture(self):
        docs = {}
        provision = "implementation/p09/evidence/p09-139-formula-issuer-registry-provision.source-progress.v1.json"
        reads = "implementation/p09/evidence/p09-137-formula-issuer-registry-reads.source-progress.v1.json"
        management = "implementation/p09/evidence/p09-138-formula-issuer-registry-management.source-progress.v1.json"
        docs[subject.LEGACY+"/p135-case-001-attempt-001.json"] = {"protected_executables": [pin(f"target/preserved/p{n}.exe") for n in range(23)]}
        docs[reads] = {"current_executables": [pin("target/preserved/p23.exe")], "earlier_executables_preserved": [pin("target/preserved/p24.exe")]}
        docs[management] = {"current_executable": pin("target/preserved/p25.exe")}
        docs[provision] = {"current_executable": pin("target/preserved/p26.exe"), "earlier_executables_preserved": [pin("target/preserved/p27.exe")]}
        for n in (2, 3, 4, 5):
            docs[subject.LEGACY+f"/p141-adapter-build-r{n}.json"] = {"executable_pin": pin(f"target/preserved/p{26+n}.exe")}
        docs["implementation/p09/evidence/p09-142-artifact-schema22.implementation-progress.v1.json"] = {
            "unit_runtime": {"executable_pin": pin("target/preserved/p32.exe")}}
        names = []
        for phase, count, stem in ((142, 3, "formula_registry_crypto_postgres_probe"), (143, 14, "formula_issuer_product_postgres_probe")):
            for number in range(1, count+1):
                name = subject.LEGACY+f"/p{phase}-{'root-crypto' if phase == 142 else 'issuer-product'}-build-r{number}.json"
                names.append(name)
                docs[name] = {"state": "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE", "executable_pin":
                    pin(subject.LEGACY+f"/debug/examples/{stem}-p{phase}-r{number}.exe")}
        return Reader(documents=docs), names

    def test_full_original_protected_closure_is_reconstructed_not_assumed(self):
        reader, names = self.closure_fixture()
        self.assertEqual(len(subject.protected_closure(reader, names)), 50)
        with self.assertRaises(ValueError):
            subject.protected_closure(reader, names[:-1])

    def test_historical_executable_path_substitution_is_rejected(self):
        reader, names = self.closure_fixture()
        reader.documents[names[-1]]["executable_pin"] = pin("target/preserved/wrong.exe")
        with self.assertRaisesRegex(ValueError, "CURRENT_ISSUER_HISTORY_EXECUTABLE_SCOPE"):
            subject.protected_closure(reader, names)

    def test_isolated_target_contract_is_read_only_and_preserves_legacy(self):
        before = (c.ROOT/subject.CURRENT_TARGET).exists()
        contract = subject.target_contract(c.ROOT)
        self.assertEqual(contract["target_directory"], "target/p09-149-current-issuer-build")
        self.assertTrue(contract["legacy_target_preserved"])
        self.assertFalse(contract["new_target_created_by_this_audit"] or contract["compiler_run"])
        self.assertEqual((c.ROOT/subject.CURRENT_TARGET).exists(), before)

    def test_current_script_has_paced_admission_final_hash_and_no_child_write_path(self):
        text = (c.ROOT/subject.EXTRA[0]).read_text(encoding="utf-8")
        self.assertIn("resources.admit()", text)
        self.assertIn("reader.finish()", text)
        self.assertIn("SOURCE_BUILD_MISSING", text)
        self.assertIn("rust_inputs(root, checkpoint) == actual_rust", text)
        self.assertNotIn("subprocess.Popen", text)
        self.assertNotIn(".mkdir(", text)
        self.assertNotIn("Get-FileHash", text)
        self.assertIn('destination.open("x", encoding="utf-8")', text)

    def test_actual_parent_schema_failure_and_changed_preimages_are_preserved(self):
        archive = json.loads((c.ROOT/subject.EXTRA[-2]).read_text(encoding="utf-8"))
        self.assertEqual(len(archive["files"]), 3)
        for row in archive["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]))
            self.assertEqual(len(raw), row["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
        failure = json.loads((c.ROOT/subject.EXTRA[-1]).read_text())
        self.assertEqual(failure["state"], "STOPPED_OR_FAILED_NOT_ACCEPTED")
        self.assertFalse(failure["current_build_input_candidate_accepted"])
        self.assertFalse(failure["compiler_build_binding_accepted"])
