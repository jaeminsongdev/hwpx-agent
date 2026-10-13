"""Small in-memory fixtures only; never queries Docker or starts a subprocess."""
import ast
import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import bounded_container_absence as subject

REFS = ["a" * 64, "hwpx-p148-12345678-1234-1234-1234-123456789abc"]
DOCKER = "C:/fixture/docker.exe"
ERROR = "fixture_absence_rejected"


def missing(references):
    return "".join(f"Error: No such object: {reference}\n" for reference in references)


class BoundedContainerAbsenceTests(unittest.TestCase):
    def accepted(self, code=1, output="", errors=None, references=REFS):
        return subject.validate_absence(code, output, missing(references) if errors is None else errors,
            references, ERROR)

    def environment(self):
        kernel = SimpleNamespace(**{name: Mock(return_value=True) for name in
            ("AssignProcessToJobObject", "TerminateJobObject", "CloseHandle", "ReleaseMutex")})
        kernel.CreateMutexW = Mock(return_value=101)
        windows = SimpleNamespace(k=kernel, job=Mock(return_value=102),
            accounting=Mock(return_value={"active_processes": 0, "peak_job_private_percent": 0.1}),
            sample=Mock(return_value={"system_cpu_percent": 10, "available_ram_percent": 40,
                "commit_used_percent": 50}))
        process = SimpleNamespace(_handle=103, stdin=io.BytesIO(), stdout=io.BytesIO(), stderr=io.BytesIO(),
            returncode=1, poll=Mock(return_value=1), wait=Mock(return_value=1), kill=Mock())
        capture = SimpleNamespace(communicate=Mock(return_value=("", missing(REFS))),
            progress=Mock(), close=Mock())
        return windows, process, capture

    def run_fixture(self, windows, process, capture, checkpoint=lambda: None):
        with patch.object(subject, "Windows", return_value=windows), \
                patch.object(subject.subprocess, "Popen", return_value=process) as launch, \
                patch.object(subject, "BoundedProcessCapture", return_value=capture) as bounded:
            result = subject.inspect_absence(DOCKER, REFS, checkpoint, ERROR)
        return result, launch, bounded

    def test_readonly_generic_batch_arguments(self):
        self.assertEqual(subject.inspect_arguments(DOCKER, REFS),
            [DOCKER, "inspect", "--format", "{{.Id}}", *REFS])
        self.assertNotIn("--type", subject.inspect_arguments(DOCKER, REFS))
        for executable in ("docker.exe", "C:/fixture/other.exe", "C:/fixture/docker.cmd"):
            with self.assertRaises(ValueError):
                subject.inspect_arguments(executable, REFS)

    def test_closed_unique_reference_scope(self):
        p146 = REFS[1].replace("p148", "p146")
        self.assertEqual(subject.references_checked([REFS[0], p146]), [REFS[0], p146])
        for references in ([], REFS * 2, ["--help"], ["foreign-container"], [False], ["a" * 63], REFS + ["A" * 64]):
            with self.subTest(references=references), self.assertRaises(ValueError):
                subject.references_checked(references)
        for prefix in ("p145", "p147", "p149", "p146--"):
            with self.assertRaises(ValueError):
                subject.references_checked([REFS[1].replace("p148", prefix)])
        with self.assertRaises(ValueError):
            subject.references_checked([f"{number:064x}" for number in range(33)])

    def test_every_missing_identity_is_bound_order_independent(self):
        self.assertEqual(self.accepted(errors=missing(list(reversed(REFS)))),
            [{"reference": reference, "absent": True} for reference in REFS])
        self.accepted(errors=missing(REFS).replace("No such object", "No such container"))

    def test_missing_duplicate_or_foreign_response_rejected(self):
        for responses in (REFS[:1], [REFS[0]] * 2, [REFS[0], "b" * 64], REFS + ["b" * 64]):
            with self.assertRaisesRegex(ValueError, "^" + ERROR + "$"):
                self.accepted(errors=missing(responses))

    def test_present_or_success_or_coerced_status_rejected(self):
        for code, output in ((0, ""), (False, ""), ("1", ""), (1, "existing-id\n"), (1, " \n")):
            with self.assertRaises(ValueError):
                self.accepted(code=code, output=output)

    def test_daemon_extra_or_raw_diagnostics_fail_closed(self):
        for errors in ("", "Cannot connect to Docker daemon", missing(REFS) + "private-value-placeholder\n",
                "Error: No such object: foreign-value\n", missing(REFS) + "\n"):
            with self.assertRaisesRegex(ValueError, "^" + ERROR + "$"):
                self.accepted(errors=errors)

    def test_output_budget_is_rejected_not_truncated(self):
        with self.assertRaisesRegex(ValueError, "^" + ERROR + "$"):
            self.accepted(errors="x" * (subject.LIMIT + 1))
        self.assertEqual(subject.LIMIT, 32768)
        self.assertEqual(subject.TIMEOUT_SECONDS, 10)

    def test_success_assigns_job_before_go_and_capture_then_cleans(self):
        windows, process, capture = self.environment()
        order = []
        windows.k.AssignProcessToJobObject.side_effect = lambda *args: order.append("assign") or True
        def capture_started(child):
            order.append("capture")
            request = child.stdin.getvalue().decode("ascii").splitlines()
            self.assertEqual(request[0], "P149_ABSENCE_GO")
            self.assertEqual(json.loads(request[1]), {"docker": DOCKER, "references": REFS})
            self.assertEqual(order, ["checkpoint", "assign", "checkpoint", "capture"])
            return capture
        with patch.object(subject, "Windows", return_value=windows), \
                patch.object(subject.subprocess, "Popen", return_value=process) as launch, \
                patch.object(subject, "BoundedProcessCapture", side_effect=capture_started):
            result = subject.inspect_absence(DOCKER, REFS, lambda: order.append("checkpoint"), ERROR)
        self.assertEqual(result, self.accepted())
        self.assertEqual(launch.call_count, 1)  # waiting worker, never Docker in parent
        self.assertEqual(launch.call_args.args[0][-1], "--owned-worker")
        windows.k.TerminateJobObject.assert_called_once_with(102, 1)
        windows.accounting.assert_called_with(102)
        self.assertEqual(windows.k.CloseHandle.call_count, 2)
        capture.close.assert_called_once()
        process.kill.assert_not_called()

    def test_assignment_failure_never_sends_go_or_starts_capture(self):
        windows, process, capture = self.environment()
        windows.k.AssignProcessToJobObject.return_value = False
        process.poll.return_value = None
        with self.assertRaisesRegex(ValueError, "^absence_job_assignment_failed$"):
            self.run_fixture(windows, process, capture)
        self.assertTrue(process.stdin.closed)
        process.kill.assert_called_once()
        capture.communicate.assert_not_called()
        windows.k.CloseHandle.assert_called()

    def test_checkpoint_stop_after_assignment_never_releases_worker(self):
        windows, process, capture = self.environment()
        checkpoint = Mock(side_effect=[None, ValueError("fixture_stop")])
        with self.assertRaisesRegex(ValueError, "^fixture_stop$"):
            self.run_fixture(windows, process, capture, checkpoint)
        capture.communicate.assert_not_called()
        self.assertTrue(process.stdin.closed)
        windows.k.TerminateJobObject.assert_called_once()

    def test_output_overflow_during_timeout_stops_owned_job(self):
        windows, process, capture = self.environment()
        capture.communicate.side_effect = subprocess.TimeoutExpired("fixture", 0.25)
        capture.progress.side_effect = ValueError("live_progress_output_limit")
        with self.assertRaisesRegex(ValueError, "^live_progress_output_limit$"):
            self.run_fixture(windows, process, capture)
        windows.k.TerminateJobObject.assert_called_once()
        capture.close.assert_called_once()

    def test_ten_second_deadline_stops_owned_job(self):
        windows, process, capture = self.environment()
        with patch.object(subject.time, "monotonic", side_effect=[0, 11, 11]):
            with self.assertRaisesRegex(ValueError, "^absence_command_timeout$"):
                self.run_fixture(windows, process, capture)
        capture.communicate.assert_not_called()
        windows.k.TerminateJobObject.assert_called_once()

    def test_resource_emergency_stops_owned_job(self):
        windows, process, capture = self.environment()
        stable = dict(windows.sample.return_value)
        windows.sample.side_effect = [stable, stable, stable | {"available_ram_percent": 7}]
        capture.communicate.side_effect = subprocess.TimeoutExpired("fixture", 0.25)
        with self.assertRaisesRegex(ValueError, "^STOP_LOW_AVAILABLE_RAM$"):
            self.run_fixture(windows, process, capture)
        windows.k.TerminateJobObject.assert_called_once()

    def test_preflight_and_pre_go_resource_failure_never_authorize_docker(self):
        for stage in ("preflight", "pre_go"):
            for changes, code in (({"available_ram_percent": 7}, "STOP_LOW_AVAILABLE_RAM"),
                    ({"commit_used_percent": 97}, "STOP_SYSTEM_COMMIT_PRESSURE"),
                    ({"available_ram_percent": float("nan")}, "STOP_RESOURCE_OBSERVATION_INVALID")):
                with self.subTest(stage=stage, code=code):
                    windows, process, capture = self.environment()
                    stable = dict(windows.sample.return_value)
                    windows.sample.side_effect = ([stable] if stage == "pre_go" else []) + [stable | changes]
                    process.stdin.write = Mock(wraps=process.stdin.write)
                    with patch.object(subject, "Windows", return_value=windows), \
                            patch.object(subject.subprocess, "Popen", return_value=process) as launch, \
                            patch.object(subject, "BoundedProcessCapture", return_value=capture) as bounded:
                        with self.assertRaisesRegex(ValueError, "^"+code+"$"):
                            subject.inspect_absence(DOCKER, REFS, lambda: None, ERROR)
                    self.assertEqual(launch.call_count, 1 if stage == "pre_go" else 0)
                    bounded.assert_not_called()
                    process.stdin.write.assert_not_called()
                    if stage == "pre_go":
                        windows.k.TerminateJobObject.assert_called_once()
                    else:
                        windows.job.assert_not_called()

    def test_fast_completion_observes_global_and_job_budgets_and_keeps_hot_count(self):
        for changes, job_changes, code in (({"available_ram_percent": 7}, {}, "STOP_LOW_AVAILABLE_RAM"),
                ({"commit_used_percent": 97}, {}, "STOP_SYSTEM_COMMIT_PRESSURE"),
                ({"system_cpu_percent": float("nan")}, {}, "STOP_RESOURCE_OBSERVATION_INVALID"),
                ({}, {"peak_job_private_percent": 7.1}, "STOP_OWNED_JOB_MEMORY_BUDGET")):
            with self.subTest(code=code):
                windows, process, capture = self.environment()
                stable = dict(windows.sample.return_value)
                windows.sample.side_effect = [stable, stable, stable | changes]
                windows.accounting.return_value.update(job_changes)
                with self.assertRaisesRegex(ValueError, "^"+code+"$"):
                    self.run_fixture(windows, process, capture)
                capture.communicate.assert_called_once()
                windows.k.TerminateJobObject.assert_called_once()
                capture.close.assert_called_once()
        windows, process, capture = self.environment()
        windows.sample.return_value["system_cpu_percent"] = 60
        self.assertEqual(self.run_fixture(windows, process, capture)[0], self.accepted())
        self.assertEqual(windows.sample.call_count, 3)
        windows, process, capture = self.environment()
        windows.sample.return_value["system_cpu_percent"] = 100
        capture.communicate.side_effect = [subprocess.TimeoutExpired("fixture", .25), ("", missing(REFS))]
        with self.assertRaisesRegex(ValueError, "^STOP_SUSTAINED_SYSTEM_CPU$"):
            self.run_fixture(windows, process, capture)
        self.assertEqual(windows.sample.call_count, 4)
        windows.k.TerminateJobObject.assert_called_once()

    def test_cleanup_failure_cannot_return_absence_success(self):
        windows, process, capture = self.environment()
        windows.k.TerminateJobObject.return_value = False
        with self.assertRaisesRegex(ValueError, "^absence_cleanup_not_confirmed$"):
            self.run_fixture(windows, process, capture)
        windows.k.CloseHandle.assert_called()

    def test_initial_checkpoint_never_starts_any_process(self):
        windows, process, capture = self.environment()
        with patch.object(subject.subprocess, "Popen") as launch, patch.object(subject, "Windows") as setup:
            with self.assertRaisesRegex(ValueError, "^fixture_stop$"):
                subject.inspect_absence(DOCKER, REFS, Mock(side_effect=ValueError("fixture_stop")), ERROR)
        launch.assert_not_called()
        setup.assert_not_called()

    def test_owned_kill_error_still_closes_job_and_mutex_and_rejects(self):
        windows, process, capture = self.environment()
        process.poll.return_value = None
        process.kill.side_effect = OSError("fixture-private-error")
        with self.assertRaisesRegex(ValueError, "^absence_cleanup_not_confirmed$"):
            self.run_fixture(windows, process, capture)
        self.assertEqual(windows.k.CloseHandle.call_count, 2)
        windows.k.ReleaseMutex.assert_called_once()
        capture.close.assert_called_once()
        windows.accounting.assert_called_with(102)

    def test_worker_rejects_missing_go_without_docker(self):
        with patch.object(subject, "Windows"), patch.object(subject.sys, "stdin", io.StringIO("wrong\n")), \
                patch.object(subject.subprocess, "call") as docker:
            with self.assertRaisesRegex(ValueError, "^absence_worker_not_authorized$"):
                subject.worker()
        docker.assert_not_called()

    def test_auditor_only_batches_existing_absence_checks(self):
        archive = subject.ROOT / "implementation/p09/source-archive/p09-149-pre-batch-absence-audit/source-preimages.v1.json"
        row = json.loads(archive.read_text(encoding="utf-8"))["files"][0]
        raw = base64.b64decode(row["base64"], validate=True)
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (row["bytes"], row["sha256"]))
        old = ast.parse(raw.decode("utf-8"))
        current = ast.parse((subject.ROOT / row["path"]).read_text(encoding="utf-8"))
        functions = lambda tree: {node.name: node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name != "audit"}
        before, after = functions(old), functions(current)
        self.assertEqual(set(before), set(after))
        for name, original in before.items():
            actual = copy.deepcopy(after[name])
            if name == "validate_case":
                # 현재 r4 resource 계약의 명시된 분기만 합성한다. default legacy와
                # 나머지 whole 함수 AST는 아래 exact 비교를 그대로 유지한다.
                original = copy.deepcopy(original)
                self.assertEqual(original.args.kwonlyargs, [])
                self.assertEqual(original.args.kw_defaults, [])
                original.args.kwonlyargs.append(ast.arg(arg="scheme"))
                original.args.kw_defaults.append(ast.Constant(value="legacy"))
                original.body.insert(0, ast.parse(
                    'require(scheme in {"legacy", "current_r4"}, "authority_build_scheme_invalid")').body[0])
                policy = next(i for i, node in enumerate(original.body) if isinstance(node, ast.Assign)
                    and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "policy")
                original.body.insert(policy+1, ast.parse(
                    'if scheme == "current_r4":\n'
                    '    from current_authority_sql_receipts import validate_current_resources\n'
                    '    validate_current_resources(run, build)\n'
                    '    return\n').body[0])
            if name == "authenticate_authority_delta":
                self.assertEqual(actual.args.args[-1].arg, "checkpoint")
                self.assertEqual(ast.dump(actual.args.defaults[-1]), ast.dump(ast.Constant(value=None)))
                actual.args.args.pop()
                actual.args.defaults.pop()
                self.assertEqual(ast.dump(actual.body.pop()), ast.dump(ast.parse(
                    "return formatted.audit_limits").body[0]))
                assignment = lambda node: next(n for n in node.body if isinstance(n, ast.Assign)
                    and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "formatted")
                self.assertEqual(ast.dump(assignment(actual).value), ast.dump(ast.parse(
                    'run_audit_tool("rustfmt-stdin", current, checkpoint=checkpoint)', mode="eval").body))
                assignment(actual).value = copy.deepcopy(assignment(original).value)
            self.assertEqual(ast.dump(original), ast.dump(actual), name)
        audit = next(node for node in current.body if isinstance(node, ast.FunctionDef) and node.name == "audit")
        batches = [node for node in ast.walk(audit) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name) and node.func.id == "inspect_absence"]
        self.assertEqual(len(batches), 2)
        self.assertEqual(len(batches[0].args[1].elts), 4)
        self.assertEqual(batches[1].args[1].id, "current_references")
        self.assertEqual([node.args[-1].value for node in batches],
            ["failed_run_owned_container_present", "owned_container_present"])
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "run" and isinstance(node.args[0], ast.List)
            and any(isinstance(arg, ast.Constant) and arg.value == "inspect" for arg in node.args[0].elts)
            for node in ast.walk(audit)))
        helper = ast.parse(Path(subject.__file__).read_text(encoding="utf-8"))
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"run", "communicate", "write_text", "write_bytes"}
            and not (node.func.attr == "communicate" and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "capture") for node in ast.walk(helper)))

    def test_all_other_audit_requirements_and_current_case_inventory_preserved(self):
        archive = subject.ROOT / "implementation/p09/source-archive/p09-149-pre-batch-absence-audit/source-preimages.v1.json"
        row = json.loads(archive.read_text(encoding="utf-8"))["files"][0]
        original = ast.parse(base64.b64decode(row["base64"], validate=True).decode("utf-8"))
        current = ast.parse((subject.ROOT / row["path"]).read_text(encoding="utf-8"))
        def requirements(tree):
            audit = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "audit")
            return sorted(ast.dump(node) for node in ast.walk(audit) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name) and node.func.id == "require"
                and not (isinstance(node.args[-1], ast.Constant)
                    and node.args[-1].value in {"failed_run_owned_container_present", "owned_container_present"}))
        self.assertEqual(requirements(original), requirements(current))
        def cases(tree):
            return next(node.value for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "CASES" for target in node.targets))
        self.assertEqual(ast.dump(cases(original)), ast.dump(cases(current)))
        self.assertEqual(len(cases(current).elts), 4)


if __name__ == "__main__":
    unittest.main()
