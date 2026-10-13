"""AST/source and mocked command paths only. Never executes Docker/SQL/main()."""
import ast
import base64
from collections import Counter
import copy
import ctypes
import hashlib
import io
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import conservative_maintenance as c
import bounded_process_progress as bounded
from audit_evidence_io import AuditEvidenceReader
from tests.test_sql_percentage_resources import restore_resource_only_changes

ARCHIVE = "implementation/p09/source-archive/p09-149-pre-live-sql-bounded-io/source-preimages.v1.json"
DRIVERS = ("tools/p09/run_formula_issuer_live_sql_probe.py", "tools/p09/run_formula_issuer_authority_sql_probe.py")


def dump(node):
    return ast.dump(node, include_attributes=False)


def command(tree):
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    return next(node for node in main.body if isinstance(node, ast.FunctionDef) and node.name == "command")


class SQLBoundedIOIntegrationTests(unittest.TestCase):
    def setUp(self):
        reader = AuditEvidenceReader(c.ROOT, lambda: None)
        archive = reader.json(ARCHIVE)
        self.old = {}
        for row in archive["files"]:
            raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
            self.assertEqual(len(raw), row["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
            self.old[row["path"]] = ast.parse(raw.decode("utf-8"))
        self.now = {name: ast.parse(reader.text(name)) for name in DRIVERS}
        reader.finish()
        self.now = {name: restore_resource_only_changes(tree, name) for name, tree in self.now.items()}

    def test_whole_noncommand_AST_is_original_except_helper_import_and_live_pin(self):
        for name in DRIVERS:
            old, now = copy.deepcopy(self.old[name]), copy.deepcopy(self.now[name])
            imported = next(node for node in now.body if isinstance(node, ast.ImportFrom)
                and node.module == "bounded_process_progress")
            self.assertEqual({alias.name for alias in imported.names},
                {"BoundedProcessCapture", "bounded_observation_run", "LIMIT", "MAX_OUTPUT"})
            self.assertTrue(all(alias.asname is None for alias in imported.names))
            for tree in (old, now):
                tree.body = [node for node in tree.body if not
                    (isinstance(node, ast.ImportFrom) and node.module == "bounded_process_progress")]
                main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
                main.body = [node for node in main.body if not
                    (isinstance(node, ast.FunctionDef) and node.name == "command")]
            if "live_sql" in name:
                main = next(node for node in now.body if isinstance(node, ast.FunctionDef) and node.name == "main")
                additions = next(node.value for node in main.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == "additions" for target in node.targets))
                before = len(additions.elts)
                additions.elts = [node for node in additions.elts if not
                    (isinstance(node, ast.Constant) and node.value == "tools/p09/bounded_process_progress.py")]
                self.assertEqual(before-len(additions.elts), 1)
            self.assertEqual(dump(now), dump(old), name)

    def test_protected_requires_queries_source_pins_and_limits_are_not_weakened(self):
        for name in DRIVERS:
            old, now = command(self.old[name]), command(self.now[name])
            def guards(root):
                return Counter(dump(node) for node in ast.walk(root) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name) and node.func.id == "require"
                    and not (len(node.args) >= 2 and isinstance(node.args[1], ast.Constant)
                        and node.args[1].value in {"live_progress_output_limit", "live_progress_marker_scope"}))
            before, after = guards(old), guards(now)
            self.assertFalse(before-after, name)
            queries = lambda root: [dump(node) for node in ast.walk(root) if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "activity_sql" for target in node.targets)]
            self.assertEqual(queries(now), queries(old))
            selector = next(node.value for node in ast.walk(now) if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "marker_mode" for target in node.targets))
            self.assertEqual(dump(selector), dump(ast.parse('rust and args[0] == str(ROOT / crypto_executable["path"])', mode="eval").body))
            calls = [node for node in ast.walk(now) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
            capture = next(node for node in calls if node.func.id == "BoundedProcessCapture")
            self.assertEqual({kw.arg: dump(kw.value) for kw in capture.keywords},
                {"input_text": dump(ast.Name(id="text", ctx=ast.Load())),
                 "output_limit": dump(ast.parse("LIMIT if marker_mode else MAX_OUTPUT", mode="eval").body),
                 "parse_markers": dump(ast.Name(id="marker_mode", ctx=ast.Load()))})
            self.assertEqual(sum(node.func.id == "bounded_observation_run" for node in calls), 1)
            for node in ast.walk(now):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    self.assertFalse(node.func.value.id == "process" and node.func.attr == "communicate")
                    self.assertFalse(node.func.value.id == "subprocess" and node.func.attr == "run")

    def fixture(self, name):
        process = SimpleNamespace(_handle=1, returncode=0, poll=Mock(return_value=0), wait=Mock(), kill=Mock(),
            stdin=io.BytesIO(), stdout=io.BytesIO(), stderr=io.BytesIO())
        capture = SimpleNamespace(communicate=Mock(return_value=("whole\r\nJSON\r", "stderr\r\n")),
            progress=Mock(return_value=([], [])), close=Mock(), error=None)
        def affinity(handle, first, second):
            first._obj.value = 1
            return True
        resources = SimpleNamespace(stop=SimpleNamespace(is_set=Mock(return_value=False)), reason=None,
            k=SimpleNamespace(GetProcessAffinityMask=Mock(side_effect=affinity), GetPriorityClass=Mock(return_value=0x4000)))
        module = ast.parse("def factory():\n    last_child = None\n")
        module.body[0].body.append(copy.deepcopy(command(self.now[name])))
        module.body[0].body.append(ast.Return(value=ast.Name(id="command", ctx=ast.Load())))
        fake_subprocess = SimpleNamespace(Popen=Mock(return_value=process), CompletedProcess=subprocess.CompletedProcess,
            PIPE=subprocess.PIPE, CREATE_NO_WINDOW=subprocess.CREATE_NO_WINDOW,
            BELOW_NORMAL_PRIORITY_CLASS=subprocess.BELOW_NORMAL_PRIORITY_CLASS, TimeoutExpired=subprocess.TimeoutExpired)
        namespace = dict(resources=resources, start=0, require=c.require, ROOT=c.ROOT, ctypes=ctypes,
            subprocess=fake_subprocess, time=SimpleNamespace(monotonic=Mock(return_value=1)),
            BoundedProcessCapture=Mock(return_value=capture), bounded_observation_run=Mock(),
            LIMIT=bounded.LIMIT, MAX_OUTPUT=bounded.MAX_OUTPUT,
            crypto_executable={"path": "fixture-crypto.exe"}, receipt={})
        exec(compile(ast.fix_missing_locations(module), "mocked-command-only", "exec"), namespace)
        return namespace["factory"](), namespace, process, capture, resources

    def test_generic_command_preserves_full_JSON_stdin_newlines_exit_and_cleanup(self):
        for name in DRIVERS:
            run, namespace, process, capture, _ = self.fixture(name)
            result = run(["fixture-command"], text="한글\nSQL")
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "whole\nJSON\n", "stderr\n"))
            namespace["BoundedProcessCapture"].assert_called_once_with(process,
                input_text="한글\nSQL", output_limit=bounded.MAX_OUTPUT, parse_markers=False)
            process.wait.assert_called_once_with(timeout=2)
            capture.close.assert_called_once()
            namespace["bounded_observation_run"].assert_not_called()

    def test_fast_resource_stop_overflow_and_crypto_mode_cannot_bypass_barriers(self):
        for name in DRIVERS:
            run, namespace, process, capture, resources = self.fixture(name)
            resources.stop.is_set.side_effect = [False, True]
            with self.assertRaisesRegex(ValueError, "^resource_stop$"):
                run(["fixture-command"])
            capture.close.assert_called_once()
            run, namespace, process, capture, _ = self.fixture(name)
            capture.communicate.side_effect = ValueError("live_progress_output_limit")
            with self.assertRaisesRegex(ValueError, "^live_progress_output_limit$"):
                run(["fixture-command"])
            capture.close.assert_called_once()
            run, namespace, process, capture, _ = self.fixture(name)
            result = run([str(c.ROOT / "fixture-crypto.exe")], rust=True)
            namespace["BoundedProcessCapture"].assert_called_once_with(process,
                input_text=None, output_limit=bounded.LIMIT, parse_markers=True)
            self.assertEqual(result.stdout, "whole\r\nJSON\r")

    def test_observation_capture_bounds_early_overflow_and_normalizes_full_EOF(self):
        process = SimpleNamespace(returncode=0, poll=Mock(return_value=0), wait=Mock(), kill=Mock())
        capture = SimpleNamespace(communicate=Mock(return_value=("[]\r\n", "err\r")), progress=Mock(), close=Mock())
        with patch.object(bounded.subprocess, "Popen", return_value=process), \
                patch.object(bounded, "BoundedProcessCapture", return_value=capture) as constructor:
            result = bounded.bounded_observation_run(["fixture-observation"], cwd=c.ROOT)
        self.assertEqual((result.stdout, result.stderr), ("[]\n", "err\n"))
        constructor.assert_called_once_with(process, output_limit=16384, parse_markers=False)
        capture.close.assert_called_once()
        process.wait.side_effect = OSError("fixture-wait-failure")
        capture.communicate.side_effect = None
        capture.close.reset_mock()
        with patch.object(bounded.subprocess, "Popen", return_value=process), \
                patch.object(bounded, "BoundedProcessCapture", return_value=capture), self.assertRaises(OSError):
            bounded.bounded_observation_run(["fixture-observation"], cwd=c.ROOT)
        capture.close.assert_called_once()
        capture.communicate.side_effect = subprocess.TimeoutExpired("fixture", .25)
        process.wait.side_effect = None
        capture.progress.side_effect = ValueError("live_progress_output_limit")
        capture.close.reset_mock()
        with patch.object(bounded.subprocess, "Popen", return_value=process), \
                patch.object(bounded, "BoundedProcessCapture", return_value=capture), \
                self.assertRaisesRegex(ValueError, "^live_progress_output_limit$"):
            bounded.bounded_observation_run(["fixture-observation"], cwd=c.ROOT)
        capture.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
