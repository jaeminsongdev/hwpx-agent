from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]


def load(name: str, relative: str):
    specification = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


qualification = load("p15_source_qualification_test", "tools/p16/p15_source_qualification.py")
artifact_validator = load(
    "p15_artifact_validator_qualification_test", "tools/p15/validate_artifact_delivery_contract.py"
)
inspector_validator = load(
    "p15_inspector_validator_qualification_test", "tools/p15/validate_inspector_staging_contract.py"
)
widget_successor = load(
    "p16_widget_successor_qualification_test", "tools/p16/validate_widget_shell_successor.py"
)


class P15SourceQualificationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="hwpx-p15-source-qualification-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        integration = qualification.load_integrated_validator()
        self.integration = integration.verified_replacements(ROOT)
        integrated_patch = patch.object(
            qualification, "integrated_replacements", return_value=self.integration
        )
        integrated_patch.start()
        self.addCleanup(integrated_patch.stop)
        postgres = qualification.load_postgres_validator()
        postgres_patch = patch.object(
            postgres, "integrated_replacements", return_value=self.integration
        )
        postgres_patch.start()
        self.addCleanup(postgres_patch.stop)
        loader_patch = patch.object(qualification, "load_postgres_validator", return_value=postgres)
        loader_patch.start()
        self.addCleanup(loader_patch.stop)
        paths = set(postgres.RUNTIME_PATHS) | set(postgres.GUARD_PATHS) | {
            postgres.PREDECESSOR_PATH,
            postgres.CONTRACT_PATH,
            f"{postgres.BASE}/current-db.json",
            f"{postgres.BASE}/independent-db.json",
            qualification.CONTRACT_PATH,
            qualification.P14_CANCEL_CONTRACT,
            qualification.P15_ARTIFACT_CONTRACT,
            qualification.P15_AUTH_CONTRACT,
            qualification.P15_ASYNC_CONTRACT,
            qualification.P15_ERROR_CONTRACT,
            qualification.P15_HANDLER_CONTRACT,
            qualification.P15_INSPECTOR_CONTRACT,
            qualification.P15_QUOTA_CONTRACT,
            qualification.P15_TELEMETRY_CONTRACT,
            qualification.P16_WIDGET_CONTRACT,
            *qualification.PLAN_AUTH_PATHS,
            *qualification.GUARD_PATHS,
        }
        paths.update(integration.verification_paths(ROOT))
        for relative in paths:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)

        artifact = json.loads((ROOT / qualification.P15_ARTIFACT_CONTRACT).read_bytes())
        auth = json.loads((ROOT / qualification.P15_AUTH_CONTRACT).read_bytes())
        cancel = json.loads((ROOT / qualification.P14_CANCEL_CONTRACT).read_bytes())
        async_contract = json.loads((ROOT / qualification.P15_ASYNC_CONTRACT).read_bytes())
        error_contract = json.loads((ROOT / qualification.P15_ERROR_CONTRACT).read_bytes())
        handler_contract = json.loads((ROOT / qualification.P15_HANDLER_CONTRACT).read_bytes())
        inspector = json.loads((ROOT / qualification.P15_INSPECTOR_CONTRACT).read_bytes())
        telemetry = json.loads((ROOT / qualification.P15_TELEMETRY_CONTRACT).read_bytes())
        quota = json.loads((ROOT / qualification.P15_QUOTA_CONTRACT).read_bytes())
        widget = json.loads((ROOT / qualification.P16_WIDGET_CONTRACT).read_bytes())
        artifact_locks = {entry["path"]: entry["sha256"] for entry in artifact["source_locks"]}
        auth_locks = {entry["path"]: entry["sha256"] for entry in auth["source_locks"]}
        cancel_locks = {entry["path"]: entry["sha256"] for entry in cancel["source_files"]}
        async_locks = {entry["path"]: entry["sha256"] for entry in async_contract["source_locks"]}
        error_locks = {entry["path"]: entry["sha256"] for entry in error_contract["source_locks"]}
        handler_locks = {entry["path"]: entry["sha256"] for entry in handler_contract["source_locks"]}
        inspector_locks = {entry["path"]: entry["sha256"] for entry in inspector["source_locks"]}
        telemetry_locks = {entry["path"]: entry["sha256"] for entry in telemetry["source_locks"]}
        quota_locks = {entry["path"]: entry["sha256"] for entry in quota["source_locks"]}
        widget_locks = {entry["path"]: entry["sha256"] for entry in widget["source_locks"]}
        self.history = {}
        for relative in qualification.ARTIFACT_PATHS:
            self.history[(qualification.P15_ARTIFACT_REVISION, relative)] = artifact_locks[relative]
        for relative in qualification.AUTH_PATHS:
            self.history[(qualification.P15_AUTH_REVISION, relative)] = auth_locks[relative]
        for relative in qualification.CANCEL_PATHS:
            self.history[(qualification.P14_CANCEL_REVISION, relative)] = cancel_locks[relative]
        for relative in qualification.ASYNC_PATHS:
            self.history[(qualification.P15_ASYNC_REVISION, relative)] = async_locks[relative]
        for relative in qualification.ERROR_PATHS:
            self.history[(qualification.P15_ERROR_REVISION, relative)] = error_locks[relative]
        for relative in qualification.HANDLER_PATHS:
            self.history[(qualification.P15_HANDLER_REVISION, relative)] = handler_locks[relative]
        for relative in qualification.INSPECTOR_PATHS:
            self.history[(qualification.P15_INSPECTOR_REVISION, relative)] = inspector_locks[relative]
        for relative in qualification.TELEMETRY_PATHS:
            self.history[(qualification.P15_TELEMETRY_REVISION, relative)] = telemetry_locks[relative]
        for relative in qualification.QUOTA_PATHS:
            self.history[(qualification.P15_QUOTA_REVISION, relative)] = quota_locks[relative]
        for relative in qualification.WIDGET_PATHS:
            self.history[(qualification.P16_WIDGET_REVISION, relative)] = widget_locks[relative]
        for relative in qualification.PLAN_AUTH_PATHS:
            observed = qualification.digest((ROOT / relative).read_bytes())
            pair = self.integration.get(relative)
            self.history[(qualification.P16_PLAN_AUTH_REVISION, relative)] = (
                pair[0] if pair is not None and pair[1] == observed else observed
            )

    def historical(self, _root: Path, revision: str, relative: str) -> str:
        return self.history[(revision, relative)]

    def verified(self, name: str):
        with patch.object(qualification, "source_at_revision", side_effect=self.historical):
            return qualification.verified_context(self.root, name)

    def write_contract(self, value) -> None:
        (self.root / qualification.CONTRACT_PATH).write_text(
            json.dumps(value), encoding="utf-8"
        )

    def test_exact_contexts_admit_only_declared_paths(self):
        self.assertEqual(set(self.verified("p15_artifact")), set(qualification.ARTIFACT_PATHS))
        self.assertEqual(set(self.verified("p15_auth")), set(qualification.AUTH_PATHS))
        self.assertEqual(set(self.verified("p14_cancel")), set(qualification.CANCEL_PATHS))
        self.assertEqual(set(self.verified("p15_async")), set(qualification.ASYNC_PATHS))
        self.assertEqual(set(self.verified("p15_error")), set(qualification.ERROR_PATHS))
        self.assertEqual(set(self.verified("p15_handler")), set(qualification.HANDLER_PATHS))
        self.assertEqual(set(self.verified("p15_inspector")), set(qualification.INSPECTOR_PATHS))
        self.assertEqual(set(self.verified("p15_telemetry")), set(qualification.TELEMETRY_PATHS))
        self.assertEqual(set(self.verified("p15_quota")), set(qualification.QUOTA_PATHS))
        self.assertEqual(set(self.verified("p16_widget")), set(qualification.WIDGET_PATHS))

    def test_all_replacements_bind_different_predecessor_and_successor_hashes(self):
        for name in (
            "p14_cancel", "p15_artifact", "p15_auth", "p15_async", "p15_error", "p15_handler", "p15_inspector",
            "p15_quota", "p15_telemetry", "p16_widget",
        ):
            for before, after in self.verified(name).values():
                self.assertNotEqual(before, after)

    def test_postgres_runtime_drift_rejects(self):
        target = self.root / "crates/artifact-service/src/lib.rs"
        target.write_bytes(target.read_bytes() + b"\n// drift\n")
        with self.assertRaisesRegex(ValueError, "source.runtime_digest"):
            self.verified("p15_artifact")

    def test_plan_authorization_source_drift_rejects(self):
        target = self.root / qualification.PLAN_AUTH_PATHS[0]
        target.write_bytes(target.read_bytes() + b"\n# drift\n")
        with self.assertRaisesRegex(qualification.QualificationError, "history.plan_auth"):
            self.verified("p15_artifact")

    def test_guard_source_drift_rejects_contract_exact(self):
        target = self.root / qualification.GUARD_PATHS[-1]
        target.write_bytes(target.read_bytes() + b"\nchanged\n")
        with self.assertRaisesRegex(qualification.QualificationError, "contract.exact"):
            self.verified("p15_artifact")

    def test_each_predecessor_contract_is_immutable(self):
        for relative in (
            qualification.P15_ARTIFACT_CONTRACT,
            qualification.P14_CANCEL_CONTRACT,
            qualification.P15_AUTH_CONTRACT,
            qualification.P15_ASYNC_CONTRACT,
            qualification.P15_ERROR_CONTRACT,
            qualification.P15_HANDLER_CONTRACT,
            qualification.P15_INSPECTOR_CONTRACT,
            qualification.P15_QUOTA_CONTRACT,
            qualification.P15_TELEMETRY_CONTRACT,
            qualification.P16_WIDGET_CONTRACT,
            qualification.POSTGRES_CONTRACT,
        ):
            with self.subTest(relative=relative):
                original = (self.root / relative).read_bytes()
                (self.root / relative).write_bytes(original + b" ")
                with self.assertRaises(ValueError):
                    self.verified("p15_artifact")
                (self.root / relative).write_bytes(original)

    def test_historical_predecessor_mismatch_rejects(self):
        with patch.object(qualification, "source_at_revision", return_value="0" * 64):
            with self.assertRaisesRegex(qualification.QualificationError, "history"):
                qualification.verified_context(self.root, "p15_artifact")

    def test_claim_promotion_unknown_context_and_extra_path_reject(self):
        with patch.object(qualification, "source_at_revision", side_effect=self.historical):
            baseline = qualification.expected_contract(self.root)
        mutations = []
        promoted = copy.deepcopy(baseline)
        promoted["claims"]["p15_phase_retested"] = True
        mutations.append(promoted)
        extra = copy.deepcopy(baseline)
        extra["contexts"]["p15_artifact"].append(extra["contexts"]["p15_artifact"][0])
        mutations.append(extra)
        unknown = copy.deepcopy(baseline)
        unknown["contexts"]["allow_any"] = []
        mutations.append(unknown)
        for value in mutations:
            self.write_contract(value)
            # The integration predecessor may reject the changed P15 contract before the
            # inner validator reaches its own byte-for-byte comparison; either path is fail-closed.
            with self.assertRaises(ValueError):
                self.verified("p15_artifact")

    def test_missing_or_unknown_context_rejects(self):
        with self.assertRaisesRegex(qualification.QualificationError, "contract.context"):
            self.verified("unknown")

    def test_writer_never_overwrites_contract(self):
        target = self.root / qualification.CONTRACT_PATH
        original = target.read_bytes()
        output = io.StringIO()
        with patch.object(qualification, "ROOT", self.root), patch.object(
            qualification, "source_at_revision", side_effect=self.historical
        ), patch("sys.argv", ["qualification", "--write"]), contextlib.redirect_stdout(output):
            self.assertEqual(qualification.main(), 1)
        self.assertEqual(target.read_bytes(), original)
        self.assertNotIn(str(self.root), output.getvalue())

    def test_current_artifact_and_inspector_chains_validate(self):
        self.assertEqual(artifact_validator.validate(ROOT), [])
        self.assertEqual(inspector_validator.validate(ROOT), [])

    def test_artifact_chain_fails_closed_without_exact_qualification(self):
        with patch.object(
            artifact_validator, "validate_p16_source_qualification", return_value={}
        ), patch.object(
            artifact_validator, "validate_current_source_qualification", return_value={}
        ), patch.object(
            artifact_validator, "validate_frozen_p16_source_qualification", return_value={}
        ):
            errors = artifact_validator.validate(ROOT)
        self.assertTrue(any(error.startswith("source_lock[") for error in errors))

    def test_widget_successor_accepts_only_the_exact_predecessor_contract(self):
        contract = json.loads(widget_successor.CONTRACT_PATH.read_bytes())
        self.assertEqual(widget_successor.validate(contract), [])
        changed = copy.deepcopy(contract)
        changed["claims"]["registered_plugin_tested"] = True
        self.assertEqual(widget_successor.validate(changed), ["successor.predecessor_exact"])

    def test_widget_successor_ignores_foreign_cached_widget_modules(self):
        contract = json.loads(widget_successor.CONTRACT_PATH.read_bytes())
        foreign_builder = types.ModuleType("build_widget_shell_contract")
        foreign_widget = types.ModuleType("widget_shell")
        with patch.dict(
            "sys.modules",
            {"build_widget_shell_contract": foreign_builder, "widget_shell": foreign_widget},
        ):
            self.assertEqual(widget_successor.validate(contract), [])

    def test_widget_successor_accepts_source_only_docs_checkout(self):
        contract = json.loads(widget_successor.CONTRACT_PATH.read_bytes())
        generated = {
            (ROOT / "web/plugin-widget/dist/widget-v1.html").resolve(),
            (ROOT / "web/plugin-widget/dist/preview.html").resolve(),
        }
        original_is_file = Path.is_file

        def generated_files_are_absent(path: Path) -> bool:
            if path.resolve() in generated:
                return False
            return original_is_file(path)

        with patch.object(Path, "is_file", new=generated_files_are_absent):
            self.assertEqual(widget_successor.validate(contract), [])

    def test_widget_successor_rejects_partial_generated_bundle(self):
        contract = json.loads(widget_successor.CONTRACT_PATH.read_bytes())
        bundle = (ROOT / "web/plugin-widget/dist/widget-v1.html").resolve()
        preview = (ROOT / "web/plugin-widget/dist/preview.html").resolve()
        original_is_file = Path.is_file

        def only_preview_exists(path: Path) -> bool:
            resolved = path.resolve()
            if resolved == bundle:
                return False
            if resolved == preview:
                return True
            return original_is_file(path)

        with patch.object(Path, "is_file", new=only_preview_exists):
            self.assertEqual(widget_successor.validate(contract), ["successor.unavailable"])

    def test_qualification_cli_has_no_phase_completion_claim(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch("sys.argv", ["qualification", "--check"]):
            self.assertEqual(qualification.main(), 0)
        value = json.loads(output.getvalue())
        self.assertIs(value["phase_complete"], False)
        self.assertEqual(value["scope"], "source_binding_successor_only")


if __name__ == "__main__":
    unittest.main()
