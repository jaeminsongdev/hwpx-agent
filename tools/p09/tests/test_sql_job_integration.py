"""Exact closed driver delta and mocked actual integrated command/observation paths."""
import ast
import base64
import copy
import ctypes
import hashlib
import io
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import conservative_maintenance as c
import bounded_process_progress as bounded
import owned_sql_job as owned
from audit_evidence_io import AuditEvidenceReader
from tests.test_live_sql_evidence_reader import restore_live_reader_driver_changes

ARCHIVE = "implementation/p09/source-archive/p09-149-pre-owned-sql-job-integration/source-preimages.v1.json"
DRIVERS = ("tools/p09/run_formula_issuer_live_sql_probe.py", "tools/p09/run_formula_issuer_authority_sql_probe.py")


def dump(node):
    return ast.dump(node, include_attributes=False)


def originals():
    reader = AuditEvidenceReader(c.ROOT, lambda: None)
    rows = {}
    for row in reader.json(ARCHIVE)["files"]:
        raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
        c.require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], "owned_SQL_preimage_drift")
        rows[row["path"]] = ast.parse(raw.decode("utf-8"))
    reader.finish()
    return rows


def command(tree):
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    return next(node for node in main.body if isinstance(node, ast.FunctionDef) and node.name == "command")


def expected_command(old):
    expected = copy.deepcopy(old)
    launch = ast.parse('''def checkpoint():
    if not cleanup:
        require(not resources.stop.is_set(), resources.reason or "resource_stop")
        require(time.monotonic() - start < 240, "adapter_total_time_limit")
factory = OwnedSQLJobFactory(windows=resources.windows,
    allowed_executables=[docker, str(ROOT / executable["path"]), str(ROOT / crypto_executable["path"])],
    checkpoint=checkpoint, record=lambda profiles: record_owned_jobs(receipt, profiles))
''').body
    index = next(i for i, node in enumerate(expected.body) if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "process" for t in node.targets))
    expected.body[index].value.func = ast.Name(id="factory", ctx=ast.Load())
    expected.body[index:index] = launch
    runtime = next(node for node in expected.body if isinstance(node, ast.Try))
    communicate_try = next(node for node in ast.walk(runtime) if isinstance(node, ast.Try)
        and any(isinstance(handler.type, ast.Attribute) and handler.type.attr == "TimeoutExpired" for handler in node.handlers))
    observe = ast.parse("process.observe()").body[0]
    communicate_try.body.insert(1, copy.deepcopy(observe))
    communicate_try.handlers[0].body.insert(0, copy.deepcopy(observe))
    observation = next(node for node in ast.walk(communicate_try) if isinstance(node, ast.Try)
        and any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "bounded_observation_run"
            for n in ast.walk(node)) and node is not communicate_try)
    observation.handlers.insert(0, ast.ExceptHandler(type=ast.Name(id="OwnedSQLJobFailure", ctx=ast.Load()),
        name=None, body=[ast.Raise(exc=None, cause=None)]))
    call = next(node for node in ast.walk(communicate_try) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name) and node.func.id == "bounded_observation_run")
    call.keywords.append(ast.keyword(arg="process_factory", value=ast.Name(id="factory", ctx=ast.Load())))
    cleanup = runtime.finalbody[0]
    cleanup.finalbody = [ast.Try(body=cleanup.finalbody, handlers=[], orelse=[],
        finalbody=ast.parse("factory.close()").body)]
    return expected


def restore_owned_job_driver_changes(tree, name):
    old, projected = originals()[name], restore_live_reader_driver_changes(tree, name)
    imported = [node for node in projected.body if isinstance(node, ast.ImportFrom) and node.module == "owned_sql_job"]
    c.require(len(imported) == 1 and [(a.name, a.asname) for a in imported[0].names] ==
        [("OwnedSQLJobFactory", None), ("OwnedSQLJobFailure", None), ("record_owned_jobs", None)], "owned_SQL_import_delta")
    projected.body.remove(imported[0])
    main = next(node for node in projected.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    additions = next(node.value for node in main.body if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "additions" for t in node.targets))
    pins = [node for node in additions.elts if isinstance(node, ast.Constant) and node.value == "tools/p09/owned_sql_job.py"]
    c.require(len(pins) == 1, "owned_SQL_source_pin_delta")
    additions.elts.remove(pins[0])
    current = command(projected)
    c.require(dump(current) == dump(expected_command(command(old))), "owned_SQL_command_delta")
    main.body[main.body.index(current)] = copy.deepcopy(command(old))
    c.require(dump(projected) == dump(old), "owned_SQL_noncommand_AST_changed")
    return projected


class SQLJobIntegrationTests(unittest.TestCase):
    def setUp(self):
        reader = AuditEvidenceReader(c.ROOT, lambda: None)
        self.now = {name: ast.parse(reader.text(name)) for name in DRIVERS}
        reader.finish()

    def fixture(self, name):
        process = SimpleNamespace(_handle=1, returncode=0, poll=Mock(return_value=0), wait=Mock(), kill=Mock(), observe=Mock(),
            stdin=io.BytesIO(), stdout=io.BytesIO(), stderr=io.BytesIO())
        capture = SimpleNamespace(communicate=Mock(return_value=("whole\r\nJSON\r", "err\r\n")),
            close=Mock(), progress=Mock(return_value=([], [])), error=None)
        factory = Mock(return_value=process)
        factory.close = Mock()
        def affinity(handle, first, second):
            first._obj.value = 1
            return True
        resources = SimpleNamespace(windows=object(), checkpoint_io=Mock(), stop=SimpleNamespace(is_set=Mock(return_value=False)), reason=None,
            k=SimpleNamespace(GetProcessAffinityMask=Mock(side_effect=affinity), GetPriorityClass=Mock(return_value=0x4000)))
        module = ast.parse("def outer():\n    last_child = None\n")
        module.body[0].body += [copy.deepcopy(command(self.now[name])), ast.Return(value=ast.Name(id="command", ctx=ast.Load()))]
        namespace = dict(resources=resources, ROOT=c.ROOT, require=c.require, start=0, ctypes=ctypes,
            time=SimpleNamespace(monotonic=Mock(return_value=1)), subprocess=subprocess,
            docker="fixture-docker", executable={"path": "metadata.exe"}, crypto_executable={"path": "crypto.exe"},
            BoundedProcessCapture=Mock(return_value=capture), bounded_observation_run=Mock(),
            OwnedSQLJobFactory=Mock(return_value=factory), OwnedSQLJobFailure=owned.OwnedSQLJobFailure,
            record_owned_jobs=Mock(), receipt={}, LIMIT=bounded.LIMIT, MAX_OUTPUT=bounded.MAX_OUTPUT)
        exec(compile(ast.fix_missing_locations(module), "owned-command-mock-only", "exec"), namespace)
        return namespace["outer"](), namespace, factory, process, capture, resources

    def test_exact_whole_driver_delta_and_SQL_guard_mutation_rejection(self):
        for name in DRIVERS:
            restore_owned_job_driver_changes(self.now[name], name)
            changed = copy.deepcopy(self.now[name])
            guard = next(node for node in ast.walk(changed) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "require" and len(node.args) > 1 and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == "owned_command_timeout")
            guard.args[0] = ast.Constant(value=True)
            with self.assertRaisesRegex(ValueError, "^live_SQL_reader_AST_delta$"):
                restore_owned_job_driver_changes(changed, name)

    def test_integrated_full_input_exit_newlines_factory_and_cleanup(self):
        for name in DRIVERS:
            run, namespace, factory, process, capture, resources = self.fixture(name)
            result = run(["fixture-docker"], text="한글\nSQL")
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "whole\nJSON\n", "err\n"))
            namespace["BoundedProcessCapture"].assert_called_once_with(process, input_text="한글\nSQL",
                output_limit=bounded.MAX_OUTPUT, parse_markers=False)
            self.assertIs(namespace["OwnedSQLJobFactory"].call_args.kwargs["windows"], resources.windows)
            self.assertEqual(namespace["OwnedSQLJobFactory"].call_args.kwargs["allowed_executables"],
                ["fixture-docker", str(c.ROOT/"metadata.exe"), str(c.ROOT/"crypto.exe")])
            process.observe.assert_called_once_with()
            factory.close.assert_called_once_with()
            capture.close.assert_called_once_with()

    def test_fast_owned_stop_and_capture_cleanup_failure_always_close_factory(self):
        for name in DRIVERS:
            run, _, factory, process, capture, _ = self.fixture(name)
            process.observe.side_effect = owned.OwnedSQLJobFailure("STOP_OWNED_JOB_MEMORY_BUDGET")
            with self.assertRaisesRegex(owned.OwnedSQLJobFailure, "^STOP_OWNED_JOB_MEMORY_BUDGET$"):
                run(["fixture-docker"])
            factory.close.assert_called_once_with()
            run, _, factory, _, capture, _ = self.fixture(name)
            capture.close.side_effect = ValueError("owned_pipe_cleanup_timeout")
            with self.assertRaisesRegex(ValueError, "^owned_pipe_cleanup_timeout$"):
                run(["fixture-docker"])
            factory.close.assert_called_once_with()

    def test_wait_observation_factory_resource_failure_is_not_swallowed(self):
        for name in DRIVERS:
            run, namespace, factory, _, capture, _ = self.fixture(name)
            # Main start at1; first timeout observation at12; deadline=21.
            namespace["time"].monotonic.side_effect = [1, 1, 1, 12, 12, 12, 12]
            namespace.update(created_id="fixture-owned-id", json=__import__("json"))
            capture.communicate.side_effect = subprocess.TimeoutExpired("fixture", .25)
            namespace["bounded_observation_run"].side_effect = owned.OwnedSQLJobFailure("OWNED_SQL_TERMINATE_FAILED")
            with self.assertRaises(owned.OwnedSQLJobFailure):
                run([str(c.ROOT/"crypto.exe")], rust=True)
            self.assertIs(namespace["bounded_observation_run"].call_args.kwargs["process_factory"], factory)
            factory.close.assert_called_once_with()
            self.assertNotIn("live_wait_observations", namespace["receipt"])

    def test_observation_fast_stop_and_pipe_failure_close_owned_process(self):
        process = SimpleNamespace(returncode=0, poll=Mock(return_value=0), wait=Mock(), kill=Mock(), observe=Mock(), close=Mock())
        capture = SimpleNamespace(communicate=Mock(return_value=("[]\r\n", "")), progress=Mock(), close=Mock())
        factory = Mock(return_value=process)
        with patch.object(bounded, "BoundedProcessCapture", return_value=capture):
            result = bounded.bounded_observation_run(["fixture"], cwd=c.ROOT, process_factory=factory)
        self.assertEqual(result.stdout, "[]\n")
        process.observe.assert_called_once_with()
        process.close.assert_called_once_with()
        process.observe.side_effect = owned.OwnedSQLJobFailure("STOP_OWNED_JOB_MEMORY_BUDGET")
        process.close.reset_mock()
        with patch.object(bounded, "BoundedProcessCapture", return_value=capture), self.assertRaises(owned.OwnedSQLJobFailure):
            bounded.bounded_observation_run(["fixture"], cwd=c.ROOT, process_factory=factory)
        process.close.assert_called_once_with()

    def test_factory_memory_shares_overlap_and_failed_close_stay_closed(self):
        windows = SimpleNamespace(memory_limit=256*65536)
        children = []
        def create(args, **kwargs):
            child = SimpleNamespace(closed=False, profile={"fixture": True}, close=Mock(), windows=kwargs["windows"])
            child.close.side_effect = lambda: setattr(child, "closed", True)
            children.append(child)
            return child
        record = Mock()
        factory = owned.OwnedSQLJobFactory(windows=windows, allowed_executables=["fixture"], checkpoint=Mock(), record=record)
        options = dict(cwd=c.ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        with patch.object(owned, "ObservedOwnedSQLJobProcess", side_effect=create):
            main = factory(["fixture"], **options)
            observer = factory(["fixture"], **options)
            self.assertEqual(main.windows.memory_limit+observer.windows.memory_limit, windows.memory_limit)
            self.assertEqual(main.windows.memory_limit, 7*observer.windows.memory_limit)
            with self.assertRaisesRegex(ValueError, "^OWNED_SQL_OBSERVATION_OVERLAP$"):
                factory(["fixture"], **options)
            observer.close()
            replacement = factory(["fixture"], **options)
            self.assertEqual(replacement.windows.memory_limit, observer.windows.memory_limit)
        children[0].close.side_effect = owned.OwnedSQLJobFailure("OWNED_SQL_TERMINATE_FAILED")
        with self.assertRaises(owned.OwnedSQLJobFailure):
            factory.close()
        with self.assertRaises(owned.OwnedSQLJobFailure):
            factory.close()
        record.assert_called_once()

    def test_closed_profile_budget_and_error_redaction(self):
        receipt = {}
        owned.record_owned_jobs(receipt, [{"fixture": True}])
        self.assertEqual(receipt["owned_host_job_profiles"], [{"fixture": True}])
        with self.assertRaisesRegex(ValueError, "^OWNED_SQL_RECEIPT_PROFILE_BUDGET$"):
            owned.record_owned_jobs(receipt, [{}]*512)
        self.assertEqual(str(owned.owned_failure(ValueError("private text not saved"))), "OWNED_SQL_OPERATION_FAILED")


if __name__ == "__main__":
    unittest.main()
