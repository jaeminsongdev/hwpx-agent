"""Compiler source/mocks only. No Cargo, SQL, native child, or stress workloads."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import conservative_maintenance as c
import owned_probe_build as subject


class OwnedProbeBuildTests(unittest.TestCase):
    def output(self, **changes):
        profile = {"opt_level": "1", "debuginfo": 1, "debug_assertions": True,
            "overflow_checks": True, "test": False}
        profile.update(changes)
        rows = [{"reason": "compiler-artifact", "target": {"name": subject.EXAMPLE}, "profile": profile},
            {"reason": "build-finished", "success": True}]
        return "\n".join(json.dumps(row) for row in rows)

    def fixture(self):
        events = []
        profile = {"target_authorized": True, "job_assigned": True, "cleanup_confirmed": False,
            "owned_tree_empty": False, "job_handle_closed": False, "limits_readback": {"verified": True}}
        owned = SimpleNamespace(profile=profile, returncode=0)
        owned.observe = Mock(side_effect=lambda: events.append("observe"))
        owned.kill = Mock(side_effect=lambda: events.append("kill"))
        owned.wait = Mock(side_effect=lambda timeout: events.append("wait"))
        def close():
            events.append("job-close")
            profile.update(cleanup_confirmed=True, owned_tree_empty=True, job_handle_closed=True)
        owned.close = Mock(side_effect=close)
        capture = SimpleNamespace(communicate=Mock(return_value=(self.output(), "")), progress=Mock(),
            close=Mock(side_effect=lambda: events.append("pipe-close")))
        resources = SimpleNamespace(windows=object(), checkpoint_io=Mock())
        factory = Mock(return_value=owned)
        capture_factory = Mock(return_value=capture)
        return resources, owned, capture, factory, capture_factory, events

    def run_fixture(self, fixture, **kwargs):
        resources, owned, capture, factory, capture_factory, events = fixture
        result = subject.compile_owned(resources, "cargo-fixture.exe", "r999", 30,
            process_factory=factory, capture_factory=capture_factory, **kwargs)
        return result

    def test_complete_messages_and_non_test_checked_profile_are_required(self):
        result = subject.parse_cargo(self.output())
        self.assertTrue(result["build_finished_success"])
        self.assertFalse(result["catalog_profile"]["test"])
        for profile in ({"test": True}, {"opt_level": "0"}, {"debug_assertions": False}, {"overflow_checks": False}):
            with self.assertRaisesRegex(ValueError, "P149_COMPILER_PROFILE_SCOPE"):
                subject.parse_cargo(self.output(**profile))

    def test_unknown_malformed_missing_duplicate_and_oversize_output_fail(self):
        for output in ("not-json", "[]", '{"reason":"unexpected"}',
                self.output().splitlines()[0], self.output()+"\n"+self.output(), "x"*(subject.MAX_OUTPUT+1)):
            with self.assertRaises(ValueError):
                subject.parse_cargo(output)

    def test_warning_blocks_acceptance_and_private_message_is_never_retained(self):
        output = self.output()+"\n"+json.dumps({"reason": "compiler-message", "message":
            {"level": "warning", "code": {"code": "fixture_code"}, "message": "PRIVATE_FIXTURE_MESSAGE",
             "rendered": "PRIVATE_FIXTURE_RENDERED", "spans": [{"file_name": "PRIVATE_FIXTURE_PATH"}]}})
        result = subject.parse_cargo(output)
        self.assertEqual(result["diagnostics"], [{"level": "warning", "code": "fixture_code"}])
        self.assertNotIn("PRIVATE_FIXTURE", json.dumps(result))

    def test_diagnostics_have_strict_count_budget(self):
        message = json.dumps({"reason": "compiler-message", "message": {"level": "error", "code": None}})
        with self.assertRaisesRegex(ValueError, "P149_COMPILER_DIAGNOSTIC_BUDGET"):
            subject.parse_cargo(self.output()+"\n"+"\n".join([message]*33))

    def test_arguments_remain_locked_offline_single_job_and_named_example(self):
        args = subject.build_arguments("fixture.exe", "r999")
        self.assertEqual(args, ["fixture.exe", "rustc", "-p", "hwpx-agent-cli", "--example", subject.EXAMPLE,
            "--profile", "dev", "--locked", "--offline", "--jobs", "1", "--target-dir", str(subject.TARGET),
            "--message-format=json", "--", "-C", "extra-filename=-p143-r999"])
        env = subject.build_environment()
        self.assertEqual(env["CARGO_PROFILE_DEV_OPT_LEVEL"], "1")
        self.assertEqual(env["CARGO_PROFILE_DEV_CODEGEN_UNITS"], "16")
        self.assertEqual(env["CARGO_PROFILE_DEV_DEBUG_ASSERTIONS"], "true")
        self.assertEqual(env["CARGO_PROFILE_DEV_OVERFLOW_CHECKS"], "true")
        self.assertEqual(env["RUSTUP_AUTO_INSTALL"], "0")

    def test_fast_completion_observation_and_all_cleanup_are_required(self):
        fixture = self.fixture()
        row = self.run_fixture(fixture)
        self.assertTrue(subject.accepted(row))
        self.assertEqual(fixture[-1], ["observe", "kill", "wait", "pipe-close", "job-close"])
        self.assertEqual(fixture[3].call_args.kwargs["allowed_executables"], ["cargo-fixture.exe"])
        self.assertIs(fixture[3].call_args.kwargs["checkpoint"], fixture[0].checkpoint_io)
        self.assertEqual(fixture[4].call_args.kwargs, {"output_limit": subject.MAX_OUTPUT, "parse_markers": False})

    def test_timeout_observation_then_completion_keeps_all_checks(self):
        fixture = self.fixture()
        fixture[2].communicate.side_effect = [subprocess.TimeoutExpired("fixture", .5), (self.output(), "")]
        row = self.run_fixture(fixture)
        self.assertTrue(subject.accepted(row))
        self.assertEqual(fixture[1].observe.call_count, 2)
        fixture[2].progress.assert_called_once()

    def test_output_overflow_cannot_pass_and_always_closes_job(self):
        fixture = self.fixture()
        fixture[2].communicate.side_effect = ValueError("live_progress_output_limit")
        row = self.run_fixture(fixture)
        self.assertEqual(row["stop_reason"], "live_progress_output_limit")
        self.assertFalse(subject.accepted(row))
        fixture[1].close.assert_called_once()

    def test_job_memory_stop_after_fast_exit_cannot_pass(self):
        fixture = self.fixture()
        fixture[1].observe.side_effect = ValueError("STOP_OWNED_JOB_MEMORY_BUDGET")
        row = self.run_fixture(fixture)
        self.assertEqual(row["stop_reason"], "STOP_OWNED_JOB_MEMORY_BUDGET")
        self.assertFalse(subject.accepted(row))
        fixture[1].close.assert_called_once()

    def test_duration_stop_never_communicates_or_skips_cleanup(self):
        fixture = self.fixture()
        row = self.run_fixture(fixture, clock=Mock(side_effect=[0, 31]))
        self.assertEqual(row["stop_reason"], "STOP_COMPILER_DURATION_LIMIT")
        self.assertFalse(subject.accepted(row))
        fixture[2].communicate.assert_not_called()
        fixture[1].close.assert_called_once()

    def test_each_cleanup_failure_prevents_acceptance_and_does_not_skip_job_close(self):
        for phase in ("kill", "wait", "pipe", "job"):
            fixture = self.fixture()
            if phase == "pipe":
                fixture[2].close.side_effect = ValueError("fixture")
            else:
                getattr(fixture[1], "close" if phase == "job" else phase).side_effect = ValueError("fixture")
            row = self.run_fixture(fixture)
            self.assertFalse(subject.accepted(row))
            self.assertFalse(row["cleanup_confirmed"])
            fixture[1].close.assert_called_once()

    def test_pre_go_launch_failure_keeps_owned_failure_profile_without_private_text(self):
        fixture = self.fixture()
        error = ValueError("PRIVATE_FIXTURE_FAILURE")
        error.owned_sql_job_profile = {"target_authorized": False, "cleanup_confirmed": True}
        fixture[3].side_effect = error
        row = self.run_fixture(fixture)
        self.assertFalse(subject.accepted(row))
        self.assertFalse(row["compiler_started"])
        self.assertNotIn("PRIVATE_FIXTURE", json.dumps(row))
        self.assertTrue(row["owned_job_profile"]["cleanup_confirmed"])
        fixture[4].assert_not_called()

    def test_acceptance_rejects_each_missing_owned_kernel_and_terminal_condition(self):
        row = self.run_fixture(self.fixture())
        for field in ("cleanup_confirmed", "owned_tree_empty", "job_handle_closed", "job_assigned", "target_authorized"):
            changed = copy.deepcopy(row)
            changed["owned_job_profile"][field] = False
            self.assertFalse(subject.accepted(changed))
        changed = copy.deepcopy(row)
        changed["owned_job_profile"]["limits_readback"]["verified"] = False
        self.assertFalse(subject.accepted(changed))
        for field, value in (("exit_code", 1), ("catalog_profile", None), ("build_finished_success", False),
                ("diagnostics", [{"level": "warning"}]), ("cleanup_confirmed", False)):
            changed = copy.deepcopy(row)
            changed[field] = value
            self.assertFalse(subject.accepted(changed))

    def test_ps_historical_guards_exact_prefix_and_whole_preimage_hash_preserved(self):
        archive = json.loads((c.ROOT/subject.SOURCES[-1]).read_text(encoding="utf-8"))
        self.assertEqual(len(archive["files"]), 1)
        pin = archive["files"][0]
        raw = base64.b64decode("".join(pin["base64_chunks"]))
        self.assertEqual(len(raw), pin["bytes"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), pin["sha256"])
        old = raw.decode("utf-8-sig").replace("\r\n", "\n")
        expected = old.split("$before=Get-P09ResourceSample")[0].replace("[ValidateRange(30,900)]", "[ValidateRange(30,600)]")
        current = (c.ROOT/pin["path"]).read_text(encoding="utf-8-sig")
        self.assertEqual(current.split("# 역사적 pin/842 Rust 입력/protected EXE 검사는 위 원문 그대로 유지한다.")[0], expected)
        tail = current[len(expected):]
        self.assertNotIn("ReadToEndAsync()", tail)
        self.assertNotIn("$proc.Start()", tail)
        self.assertIn("Test-Pins $protected;$oldExact=$true;Test-Pins $freeze;$exact=$true", tail)
        self.assertIn("[IO.FileMode]::CreateNew", tail)
        self.assertIn("probe_supervisor_accepted=$supervised", tail)

    def test_fresh_target_scope_rejects_traversal_variant_and_existing_receipt(self):
        for variant, receipt in (("../r1", "irrelevant"), ("r1", "target/../outside.json"),
                ("r9999999", "irrelevant"), ("r1", "target/p09-121-resource-optimized/p143-issuer-product-build-r14.json")):
            with self.assertRaises(ValueError):
                subject.paths(variant, receipt)

    def test_shared_lock_and_failure_cleanup_fields_are_source_bound(self):
        text = (c.ROOT/"tools/p09/owned_probe_build.py").read_text(encoding="utf-8")
        self.assertIn('MUTEX = "Local\\\\HwpxAgentP149ConservativeMaintenance"', text)
        self.assertIn('reader.finish()', text)
        self.assertIn('resources.stop.is_set()', text)
        self.assertIn('resources.thread.join(2)', text)
        self.assertIn('destination.open("x", encoding="utf-8")', text)
        self.assertNotIn('subprocess.Popen(', text)

    def test_failed_acceptance_preimage_is_preserved_with_whole_length_and_hash(self):
        archive = json.loads((c.ROOT/subject.SOURCES[-2]).read_text(encoding="utf-8"))
        self.assertEqual(len(archive["files"]), 1)
        pin = archive["files"][0]
        self.assertEqual(pin["path"], "tools/p09/owned_probe_build.py")
        raw = base64.b64decode("".join(pin["base64_chunks"]))
        self.assertEqual(len(raw), pin["bytes"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), pin["sha256"])
        self.assertNotIn('and profile.get("cleanup_confirmed") is True', raw.decode("utf-8"))
