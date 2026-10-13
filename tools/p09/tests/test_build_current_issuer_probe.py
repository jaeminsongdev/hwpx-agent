"""Current target adapter and exact compiler acceptance: small fixtures, no compiler."""
import copy
import hashlib
import json
import base64
import os
import threading
import subprocess
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from unittest.mock import patch

import conservative_maintenance as c
import current_issuer_build_inputs as inputs
import owned_probe_build as compiler
import build_current_issuer_probe as subject


class BuildCurrentIssuerProbeTests(unittest.TestCase):
    def candidate(self):
        raw = (c.ROOT/subject.CANDIDATE_PIN["path"]).read_bytes()
        self.assertEqual(len(raw), subject.CANDIDATE_PIN["bytes"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), subject.CANDIDATE_PIN["sha256"])
        return json.loads(raw)

    def test_immutable_actual_candidate_full_inputs_and_target_are_required(self):
        candidate = self.candidate()
        source, helper, protected = subject.candidate_contract(candidate)
        self.assertEqual((len(source), len(helper), len(protected)), (842, 19, 50))
        self.assertFalse(candidate["compiler_build_binding_accepted"])

    def test_candidate_false_flags_or_compiled_reclassification_are_rejected(self):
        candidate = self.candidate()
        for field, value in (("current_build_input_candidate_accepted", False), ("compiler_build_binding_accepted", True),
                ("source_freeze_exact_after", False), ("build_helper_freeze_exact_after", False),
                ("protected_executables_exact_after", False), ("mutex_cleanup_confirmed", False),
                ("historical_parent_archive_verified", False), ("whole_workspace_Rust_input_coverage_enforced", False),
                ("historical_protected_closure_exact", False)):
            changed = copy.deepcopy(candidate)
            changed[field] = value
            with self.assertRaises(ValueError):
                subject.candidate_contract(changed)

    def test_candidate_source_helper_protected_count_or_delta_scope_cannot_shrink(self):
        candidate = self.candidate()
        for name in ("source_freeze", "build_helper_freeze", "protected_executables", "declared_source_delta_paths"):
            changed = copy.deepcopy(candidate)
            changed[name].pop()
            with self.assertRaises(ValueError):
                subject.candidate_contract(changed)
        candidate["target_contract"]["target_directory"] = inputs.LEGACY
        with self.assertRaises(ValueError):
            subject.candidate_contract(candidate)

    def kwargs(self):
        return {"windows": object(), "allowed_executables": ["fixture-cargo.exe"], "cwd": c.ROOT,
            "checkpoint": Mock(), "env": compiler.build_environment()}

    def test_only_target_dir_is_translated_and_owned_launch_callbacks_are_preserved(self):
        args = compiler.build_arguments("fixture-cargo.exe", "r999")
        expected = list(args)
        expected[expected.index("--target-dir")+1] = str(c.ROOT/inputs.CURRENT_TARGET)
        kwargs = self.kwargs()
        process_type = Mock()
        result = subject.launch_current(args, cargo="fixture-cargo.exe", variant="r999", process_type=process_type, **kwargs)
        self.assertIs(result, process_type.return_value)
        self.assertEqual(process_type.call_args.args, (expected,))
        self.assertIs(process_type.call_args.kwargs["checkpoint"], kwargs["checkpoint"])
        self.assertIs(process_type.call_args.kwargs["env"], kwargs["env"])
        self.assertEqual(process_type.call_args.kwargs["allowed_executables"], ["fixture-cargo.exe"])

    def test_extra_argument_or_wrong_example_cannot_reach_owned_launcher(self):
        original = compiler.build_arguments("fixture-cargo.exe", "r999")
        for args in (original+["--extra"], ["wrong.exe"]+original[1:], original[:-1]+["wrong-suffix"]):
            process_type = Mock()
            with self.assertRaises(ValueError):
                subject.launch_current(args, cargo="fixture-cargo.exe", variant="r999", process_type=process_type, **self.kwargs())
            process_type.assert_not_called()

    def test_wrong_cwd_or_executable_allowlist_cannot_reach_owned_launcher(self):
        args = compiler.build_arguments("fixture-cargo.exe", "r999")
        for field, value in (("cwd", c.ROOT/"target"), ("allowed_executables", ["wrong.exe"])):
            kwargs = self.kwargs()
            kwargs[field] = value
            process_type = Mock()
            with self.assertRaises(ValueError):
                subject.launch_current(args, cargo="fixture-cargo.exe", variant="r999", process_type=process_type, **kwargs)
            process_type.assert_not_called()

    def test_unreviewed_wrappers_flags_target_and_profile_overrides_fail_closed(self):
        env = compiler.build_environment()
        subject.validate_environment(env)
        for name in subject.OVERRIDES:
            changed = dict(env)
            changed[name] = "PRIVATE_FIXTURE_OVERRIDE"
            with self.assertRaisesRegex(ValueError, "CURRENT_COMPILER_UNREVIEWED_COMPILER_OVERRIDE"):
                subject.validate_environment(changed)
        env["CARGO_PROFILE_DEV_OVERFLOW_CHECKS"] = "false"
        with self.assertRaisesRegex(ValueError, "CURRENT_COMPILER_PROFILE_ENVIRONMENT_DRIFT"):
            subject.validate_environment(env)

    def test_fresh_output_paths_are_root_scoped_and_do_not_create_target(self):
        existed = (c.ROOT/inputs.CURRENT_TARGET).exists()
        target, receipt, executable = subject.output_paths(c.ROOT, "r999999")
        self.assertEqual(target, c.ROOT/inputs.CURRENT_TARGET)
        self.assertEqual(receipt.name, "current-issuer-build-r999999.json")
        self.assertEqual(executable.name, compiler.EXAMPLE+"-p143-r999999.exe")
        self.assertEqual(target.exists(), existed)
        for variant in ("../r1", "r0", "r0001", "r1000000", "r1/escape"):
            with self.assertRaises(ValueError):
                subject.output_paths(c.ROOT, variant)

    def accepted(self):
        return {"variant": "r999", "exit_code": 0, "stop_reason": None, "build_finished_success": True,
            "catalog_profile": {"test": False}, "diagnostics": [], "cleanup_confirmed": True,
            "source_freeze_exact_after": True, "build_helper_freeze_exact_after": True, "protected_executables_exact_after": True,
            "actual_SQL_or_native_product_executed": False, "compiler_build_binding_accepted": True,
            "executable_pin": {"path": inputs.CURRENT_TARGET+"/debug/examples/"+compiler.EXAMPLE+"-p143-r999.exe",
                "bytes": 1, "sha256": "a"*64}, "owned_job_profile": {"cleanup_confirmed": True,
                "job_assigned": True, "target_authorized": True, "owned_tree_empty": True,
                "job_handle_closed": True, "limits_readback": {"verified": True}}}

    def test_build_acceptance_requires_all_final_bindings_and_actual_owned_cleanup(self):
        row = self.accepted()
        self.assertTrue(subject.build_accepted(row))
        for field, value in (("source_freeze_exact_after", False), ("build_helper_freeze_exact_after", False),
                ("protected_executables_exact_after", False), ("executable_pin", None),
                ("actual_SQL_or_native_product_executed", True), ("variant", "r998"), ("exit_code", 1)):
            changed = copy.deepcopy(row)
            changed[field] = value
            self.assertFalse(subject.build_accepted(changed))
        row["owned_job_profile"]["cleanup_confirmed"] = False
        self.assertFalse(subject.build_accepted(row))

    def test_previous_current_exe_is_protected_and_wrong_target_is_rejected(self):
        row = dict(self.accepted(), state=subject.PASS)
        reader = type("Reader", (), {"json": lambda self, name: row})()
        names = [inputs.CURRENT_TARGET+"/current-issuer-build-r999.json"]
        pins = subject.previous_current_protection(reader, names)
        self.assertEqual(pins, [row["executable_pin"]])
        row["executable_pin"]["path"] = inputs.LEGACY+"/debug/examples/wrong.exe"
        with self.assertRaises(ValueError):
            subject.previous_current_protection(reader, names)

    def test_failed_previous_receipt_is_preserved_but_not_accepted_as_executable_evidence(self):
        row = {"state": "NOT_ACCEPTED_STOP_OR_FAILURE"}
        reader = type("Reader", (), {"json": lambda self, name: row})()
        self.assertEqual(subject.previous_current_protection(reader, ["fixture-failure.json"]), [])

    def test_source_contract_preserves_final_fresh_hash_and_checked_lock_cleanup(self):
        text = (c.ROOT/subject.OWN_SOURCES[0]).read_text(encoding="utf-8")
        self.assertIn("reader.finish()", text)
        self.assertIn("if build_accepted(row):", text)
        self.assertIn("resources.thread.join(2)", text)
        self.assertIn("resources.stop.is_set()", text)
        self.assertIn("ReleaseMutex", text)
        self.assertIn("CloseHandle", text)
        self.assertIn('destination.open("x", encoding="utf-8")', text)
        self.assertNotIn("subprocess.Popen", text)
        self.assertNotIn("ReadToEndAsync", text)
        self.assertIn("inputs.historical_receipts(c.ROOT) == legacy_names", text)
        self.assertIn("current_receipts(c.ROOT) == prior_names", text)

    def installed_cargo(self):
        home = Path(os.environ.get("RUSTUP_HOME", str(Path.home()/".rustup")))
        files = sorted((home/"toolchains").glob("*/bin/cargo.exe"))
        self.assertTrue(files)
        return home, files[0]

    def test_resolved_cargo_must_be_single_direct_file_under_configured_toolchains(self):
        home, cargo = self.installed_cargo()
        self.assertEqual(subject.cargo_output_path(str(cargo)+"\r\n", home), str(cargo))
        for output in ("", "not-an-absolute-path", str(cargo)+"\n"+str(cargo), str(c.ROOT/"Cargo.toml")):
            with self.assertRaises(ValueError):
                subject.cargo_output_path(output, home)
        with self.assertRaises(ValueError):
            subject.cargo_output_path(str(cargo), c.ROOT)

    def test_rustup_resolution_uses_only_checked_owned_readonly_command(self):
        _, cargo = self.installed_cargo()
        resources = type("Resources", (), {"windows": object(), "checkpoint_io": Mock()})()
        profile = {"cleanup_confirmed": True, "owned_tree_empty": True, "job_handle_closed": True,
            "limits_readback": {"verified": True}}
        owned = type("Owned", (), {"profile": profile})()
        process_type = Mock(return_value=owned)
        def runner(command, **kwargs):
            import subprocess
            self.assertEqual(command[-2:], ["which", "cargo"])
            self.assertEqual(kwargs["timeout"], 3)
            kwargs["process_factory"](command, cwd=kwargs["cwd"], creationflags=kwargs["creationflags"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace")
            return type("Completed", (), {"returncode": 0, "stdout": str(cargo)})()
        result, resolution = subject.resolve_cargo(resources, runner=runner, process_type=process_type)
        self.assertEqual(result, str(cargo))
        self.assertTrue(resolution["rustup_resolver_used"])
        self.assertIs(process_type.call_args.kwargs["checkpoint"], resources.checkpoint_io)
        self.assertEqual(process_type.call_args.args[0][-2:], ["which", "cargo"])
        self.assertEqual(process_type.call_args.kwargs["env"]["RUSTUP_AUTO_INSTALL"], "0")

    def test_rustup_resolver_missing_owned_profile_or_failure_is_rejected(self):
        _, cargo = self.installed_cargo()
        resources = type("Resources", (), {"windows": object(), "checkpoint_io": Mock()})()
        for code in (0, 1):
            runner = Mock(return_value=type("Completed", (), {"returncode": code, "stdout": str(cargo)})())
            with self.assertRaises(ValueError):
                subject.resolve_cargo(resources, runner=runner, process_type=Mock())

    def test_missing_cargo_hint_never_launches_resolver(self):
        runner = Mock()
        with self.assertRaisesRegex(ValueError, "CURRENT_COMPILER_CARGO_MISSING"):
            subject.resolve_cargo(object(), which=lambda name: None, runner=runner)
        runner.assert_not_called()

    def test_compiler_shim_failure_and_pre_repair_sources_are_preserved(self):
        archive = json.loads((c.ROOT/subject.OWN_SOURCES[3]).read_text(encoding="utf-8"))
        self.assertEqual(len(archive["files"]), 3)
        for row in archive["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]))
            self.assertEqual(len(raw), row["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
        failure = json.loads((c.ROOT/subject.OWN_SOURCES[4]).read_text())
        self.assertFalse(failure["compiler_started"])
        self.assertEqual(failure["stop_reason"], "OWNED_SQL_EXECUTABLE_NOT_ALLOWLISTED")
        self.assertFalse(failure["compiler_build_binding_accepted"])

    def capture_fixture(self, raw):
        capture = subject.ProgressCompilerCapture.__new__(subject.ProgressCompilerCapture)
        capture.lock = threading.Lock()
        capture.buffers = {"stderr": bytearray(raw)}
        capture.receipt = {}
        return capture

    def test_project_progress_uses_only_complete_closed_package_stage(self):
        raw = b"Compiling domain-ir v0.1.0 (PRIVATE_PATH)\nCompiling unknown-private-name v1\nChecking hwpx-package v0.1.0\nCompiling hwpx-agent-cli v0.1.0"
        capture = self.capture_fixture(raw)
        hint = subject.project_announcement(capture)
        self.assertEqual(hint, {"stage": "Checking", "package": "hwpx-package"})
        self.assertNotIn("PRIVATE", json.dumps(hint))

    def test_capture_preserves_complete_output_and_timeout_and_records_hint(self):
        capture = self.capture_fixture(b"Compiling hwpx-package v0.1.0\n")
        with patch.object(subject.BoundedProcessCapture, "communicate", return_value=("fixture-json", "fixture-stderr")):
            self.assertEqual(capture.communicate(.5), ("fixture-json", "fixture-stderr"))
        self.assertEqual(capture.receipt["last_project_cargo_announcement"], {"stage": "Compiling", "package": "hwpx-package"})
        with patch.object(subject.BoundedProcessCapture, "communicate", side_effect=subprocess.TimeoutExpired("fixture", .5)):
            with self.assertRaises(subprocess.TimeoutExpired):
                capture.communicate(.5)
        self.assertEqual(capture.receipt["last_project_cargo_announcement"]["package"], "hwpx-package")

    def test_progress_budget_and_missing_or_partial_line_never_invent_stage(self):
        for raw in (b"", b"Compiling hwpx-package", b"unknown progress\n"):
            self.assertIsNone(subject.project_announcement(self.capture_fixture(raw)))
        with self.assertRaisesRegex(ValueError, "CURRENT_COMPILER_PROGRESS_BUFFER_BUDGET"):
            subject.project_announcement(self.capture_fixture(b"x"*(compiler.MAX_OUTPUT+1)))

    def test_pre_progress_sources_and_actual_time_stop_remain_failed_evidence(self):
        archive = json.loads((c.ROOT/subject.OWN_SOURCES[5]).read_text(encoding="utf-8"))
        self.assertEqual(len(archive["files"]), 3)
        for row in archive["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]))
            self.assertEqual(len(raw), row["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
        failure = json.loads((c.ROOT/subject.OWN_SOURCES[6]).read_text())
        self.assertEqual(failure["stop_reason"], "STOP_COMPILER_DURATION_LIMIT")
        self.assertTrue(failure["owned_job_profile"]["owned_tree_empty"])
        self.assertFalse(failure["compiler_build_binding_accepted"])

    def resource_fixture(self, *, watching=True):
        row = {"system_cpu_percent": 60, "available_ram_percent": 40, "commit_used_percent": 35}
        windows = SimpleNamespace(mask=1, k=SimpleNamespace(GetCurrentProcess=Mock(return_value=1)),
            sample=Mock(return_value=row))
        resources = subject.CurrentCompilerResources(windows)
        resources.samples.append(row)
        resources.last_sample_at = 10.0
        resources.thread = SimpleNamespace(ident=1 if watching else None, is_alive=lambda: watching)
        return resources

    def test_fresh_runtime_sample_and_exact_age_boundary_keep_shared_checkpoint(self):
        for now in (10.0, 11.0, 10.0+subject.MAX_OBSERVATION_AGE_SECONDS):
            resources = self.resource_fixture()
            with patch.object(subject.time, "monotonic", return_value=now), \
                    patch.object(subject.PercentageResources, "checkpoint_io") as original:
                resources.checkpoint_io()
            original.assert_called_once_with()
            self.assertFalse(resources.stop.is_set())
        self.assertEqual(subject.MAX_OBSERVATION_AGE_SECONDS, 2.0)

    def test_alive_but_stale_runtime_watcher_stops_before_shared_checkpoint(self):
        resources = self.resource_fixture()
        with patch.object(subject.time, "monotonic", return_value=12.001), \
                patch.object(subject.PercentageResources, "checkpoint_io") as original:
            with self.assertRaisesRegex(ValueError, "^STOP_RESOURCE_OBSERVATION_STALE$"):
                resources.checkpoint_io()
        original.assert_not_called()
        self.assertTrue(resources.stop.is_set())
        self.assertEqual(resources.reason, "STOP_RESOURCE_OBSERVATION_STALE")

    def test_pre_hash_manual_sampler_refreshes_without_starting_watcher(self):
        resources = self.resource_fixture(watching=False)
        with patch.object(subject.time, "monotonic", return_value=13.0):
            resources.checkpoint_io()
        resources.windows.sample.assert_called_once_with()
        self.assertEqual(resources.last_sample_at, 13.0)
        self.assertFalse(resources.stop.is_set())

    def test_staleness_during_shared_checkpoint_is_also_rejected(self):
        resources = self.resource_fixture()
        with patch.object(subject.time, "monotonic", side_effect=[11.0, 12.001]), \
                patch.object(subject.PercentageResources, "checkpoint_io") as original:
            with self.assertRaisesRegex(ValueError, "STOP_RESOURCE_OBSERVATION_STALE"):
                resources.checkpoint_io()
        original.assert_called_once_with()
        self.assertTrue(resources.stop.is_set())

    def test_invalid_observation_timestamp_or_backwards_clock_fails_closed(self):
        for observed, now in ((True, 11), (float("nan"), 11), (float("inf"), 11),
                (10, float("nan")), (10, float("inf")), (10, True), (10, 9)):
            resources = self.resource_fixture()
            resources.last_sample_at = observed
            with patch.object(subject.time, "monotonic", return_value=now):
                with self.assertRaisesRegex(ValueError, "^STOP_RESOURCE_CLOCK_INVALID$"):
                    resources.checkpoint_io()
            self.assertEqual(resources.reason, "STOP_RESOURCE_CLOCK_INVALID")

    def test_existing_host_memory_stop_and_dead_watcher_checks_are_not_bypassed(self):
        resources = self.resource_fixture()
        resources._failed("STOP_SYSTEM_COMMIT_PRESSURE")
        with patch.object(subject.time, "monotonic", return_value=11.0):
            with self.assertRaisesRegex(ValueError, "STOP_SYSTEM_COMMIT_PRESSURE"):
                resources.checkpoint_io()
        resources = self.resource_fixture()
        resources.thread.is_alive = lambda: False
        with patch.object(subject.time, "monotonic", return_value=11.0):
            with self.assertRaisesRegex(ValueError, "STOP_RESOURCE_WATCHER_NOT_ALIVE"):
                resources.checkpoint_io()

    def test_stale_compiler_stop_preserves_closed_reason_and_owned_cleanup(self):
        from tests.test_owned_probe_build import OwnedProbeBuildTests
        suite = OwnedProbeBuildTests()
        fixture = suite.fixture()
        fixture[0].checkpoint_io.side_effect = ValueError("STOP_RESOURCE_OBSERVATION_STALE")
        row = suite.run_fixture(fixture)
        self.assertEqual(row["stop_reason"], "STOP_RESOURCE_OBSERVATION_STALE")
        self.assertFalse(compiler.accepted(row))
        fixture[1].kill.assert_called_once()
        fixture[1].wait.assert_called_once_with(timeout=2)
        fixture[2].close.assert_called_once()
        fixture[1].close.assert_called_once()

    def test_freshness_guard_is_used_by_current_build_and_recorded_in_receipt(self):
        text = (c.ROOT/subject.OWN_SOURCES[0]).read_text(encoding="utf-8")
        self.assertIn("resources = CurrentCompilerResources()", text)
        self.assertIn('"maximum_completed_resource_sample_age_seconds": MAX_OBSERVATION_AGE_SECONDS', text)
        self.assertIn("resources, cargo, args.variant, args.maximum_seconds", text)
        self.assertIn("checkpoint=resources.checkpoint_io", text)

    def test_pre_freshness_sources_keep_whole_bytes_and_original_progress_contract(self):
        archive = json.loads((c.ROOT/subject.OWN_SOURCES[7]).read_text(encoding="utf-8"))
        self.assertEqual(len(archive["files"]), 3)
        for row in archive["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
            self.assertEqual(len(raw), row["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
            if row["path"] == subject.OWN_SOURCES[0]:
                self.assertIn(b"class ProgressCompilerCapture", raw)
                self.assertIn(b"reader.finish()", raw)
                self.assertNotIn(b"class CurrentCompilerResources", raw)
