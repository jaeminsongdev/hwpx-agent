"""Percentage admission/watch and exact driver resource-only delta. No real child/SQL."""
import ast
import base64
import copy
import hashlib
import math
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import conservative_maintenance as c
import sql_percentage_resources as subject
from audit_evidence_io import AuditEvidenceReader
from tests.test_sql_job_integration import restore_owned_job_driver_changes

ARCHIVE = "implementation/p09/source-archive/p09-149-pre-sql-percentage-resource/source-preimages.v1.json"
DRIVERS = ("tools/p09/run_formula_issuer_live_sql_probe.py", "tools/p09/run_formula_issuer_authority_sql_probe.py")
PINS = {"tools/p09/sql_percentage_resources.py", "tools/p09/conservative_maintenance.py", "tools/p09/audit_evidence_io.py"}
NEW_CODES = {"STOP_SYSTEM_COMMIT_PRESSURE", "STOP_RESOURCE_OBSERVATION_INVALID",
    "DEFERRED_ALREADY_SATURATED_SYSTEM", "STOP_RESOURCE_SAMPLE_BUDGET",
    "RAM_SAMPLE_FAILED", "RAM_SAMPLE_INVALID", "CPU_SAMPLE_FAILED", "CPU_SAMPLE_INTERVAL_MISSING"}


def dump(node):
    return ast.dump(node, include_attributes=False)


def originals():
    reader = AuditEvidenceReader(c.ROOT, lambda: None)
    result = {}
    for row in reader.json(ARCHIVE)["files"]:
        raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
        c.require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"],
            "sql_resource_preimage_drift")
        result[row["path"]] = ast.parse(raw.decode("utf-8"))
    reader.finish()
    return result


def restore_resource_only_changes(tree, name):
    """Validate exact resource delta, then project for the existing whole-AST IO guard.

    No command/SQL/fixture/Gate/identity node is removed from comparison.
    """
    old, projected = originals()[name], restore_owned_job_driver_changes(tree, name)
    imported = [node for node in projected.body if isinstance(node, ast.ImportFrom)
        and node.module == "sql_percentage_resources"]
    c.require(len(imported) == 1 and [(a.name, a.asname) for a in imported[0].names] ==
        [("PercentageResources", "IdleResources"), ("admit", None), ("resource_policy", None)],
        "sql_resource_import_delta")
    c.require(not any(isinstance(node, ast.ImportFrom) and node.module == "idle_resource_admission"
        for node in projected.body), "legacy_sql_resource_import_remains")
    projected.body[projected.body.index(imported[0])] = copy.deepcopy(next(node for node in old.body
        if isinstance(node, ast.ImportFrom) and node.module == "idle_resource_admission"))
    bootstrap = next(node for node in projected.body if isinstance(node, ast.ImportFrom)
        and node.module == "run_resource_bounded_python")
    c.require([(a.name, a.asname) for a in bootstrap.names] == [("observed_limits", None)],
        "sql_resource_bootstrap_delta")
    bootstrap.names = copy.deepcopy(next(node.names for node in old.body if isinstance(node, ast.ImportFrom)
        and node.module == "run_resource_bounded_python"))
    main = next(node for node in projected.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    additions = next(node.value for node in main.body if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "additions" for t in node.targets))
    added = [node for node in additions.elts if isinstance(node, ast.Constant) and node.value in PINS]
    c.require(len(added) == 3 and {node.value for node in added} == PINS, "sql_resource_source_pin_delta")
    additions.elts = [node for node in additions.elts if node not in added]
    receipt = next(node.value for node in main.body if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "receipt" for t in node.targets))
    old_main = next(node for node in old.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    old_receipt = next(node.value for node in old_main.body if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "receipt" for t in node.targets))
    index = next(i for i, key in enumerate(receipt.keys) if isinstance(key, ast.Constant) and key.value == "resource_policy")
    c.require(dump(receipt.values[index]) == dump(ast.parse("resource_policy()", mode="eval").body),
        "sql_resource_policy_call_delta")
    old_index = next(i for i, key in enumerate(old_receipt.keys) if isinstance(key, ast.Constant) and key.value == "resource_policy")
    receipt.values[index] = copy.deepcopy(old_receipt.values[old_index])
    if "authority_sql" in name:
        old_class = next(node for node in old.body if isinstance(node, ast.ClassDef) and node.name == "AdmissionRefusal")
        current_class = next(node for node in projected.body if isinstance(node, ast.ClassDef) and node.name == "AdmissionRefusal")
        expected = copy.deepcopy(old_class)
        codes = next(node.value for node in ast.walk(expected) if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "allowed_codes" for t in node.targets))
        codes.elts.extend(ast.Constant(value=code) for code in sorted(NEW_CODES))
        diagnostic = next(node.value for node in ast.walk(expected) if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Attribute) and t.attr == "diagnostics" for t in node.targets))
        mapping = {"required_available_RAM_min_percent": "start_available_ram_min_percent",
            "maximum_commit_used_percent": "maximum_commit_used_percent",
            "already_saturated_CPU_percent": "already_saturated_cpu_percent",
            "required_consecutive_samples": "start_consecutive_samples",
            "maximum_admission_seconds": "maximum_admission_seconds"}
        keep = [(k, v) for k, v in zip(diagnostic.keys, diagnostic.values) if k.value not in
            {"required_idle_CPU_max_percent", "required_idle_RAM_min_mib", "required_consecutive_samples", "maximum_admission_seconds"}]
        for key, value in mapping.items():
            keep.append((ast.Constant(value=key), ast.parse(f"resource_policy()[{value!r}]", mode="eval").body))
        # Dict/set entry order is irrelevant to diagnostics, but every AST value is exact.
        def normalized(root):
            root = copy.deepcopy(root)
            for node in ast.walk(root):
                if isinstance(node, ast.Set):
                    node.elts.sort(key=dump)
                if isinstance(node, ast.Dict):
                    pairs = sorted(zip(node.keys, node.values), key=lambda pair: dump(pair[0]))
                    node.keys, node.values = [p[0] for p in pairs], [p[1] for p in pairs]
            return dump(root)
        diagnostic.keys, diagnostic.values = [p[0] for p in keep], [p[1] for p in keep]
        c.require(normalized(current_class) == normalized(expected), "sql_resource_refusal_delta")
        projected.body[projected.body.index(current_class)] = copy.deepcopy(old_class)
    c.require(dump(projected) == dump(old), "sql_nonresource_AST_changed")
    return projected


class SQLPercentageResourceTests(unittest.TestCase):
    def row(self, cpu=60, ram=30, commit=40):
        return {"system_cpu_percent": cpu, "available_ram_percent": ram, "commit_used_percent": commit,
            "available_ram_mib": 3000, "total_ram_mib": 10000, "time_utc": "fixture"}

    def fixture(self, rows):
        windows = SimpleNamespace(mask=1, k=SimpleNamespace(GetCurrentProcess=Mock(return_value=1)),
            sample=Mock(side_effect=rows))
        return subject.PercentageResources(windows)

    def clock(self):
        value = [0.0]
        return lambda seconds: value.__setitem__(0, value[0]+seconds), lambda: value[0]

    def test_two_driver_whole_AST_resource_only_change(self):
        reader = AuditEvidenceReader(c.ROOT, lambda: None)
        for name in DRIVERS:
            restore_resource_only_changes(ast.parse(reader.text(name)), name)
        reader.finish()

    def test_normal_CPU_and_small_machine_RAM_can_admit(self):
        resources = self.fixture([self.row(cpu=75, ram=5)]*2)
        sleep, clock = self.clock()
        self.assertEqual(resources.admit(sleep, clock), 2)
        self.assertEqual(len(resources.samples), 2)
        self.assertFalse(resources.stop.is_set())
        self.assertIsNone(resources.thread.ident)

    def test_admission_immediate_saturation_commit_and_RAM_fail_closed(self):
        for row, code in ((self.row(cpu=98), "DEFERRED_ALREADY_SATURATED_SYSTEM"),
                (self.row(commit=95), "STOP_SYSTEM_COMMIT_PRESSURE"),
                (self.row(ram=4.99), "STOP_LOW_AVAILABLE_RAM")):
            resources = self.fixture([row])
            sleep, clock = self.clock()
            with self.assertRaisesRegex(ValueError, "^"+code+"$"):
                resources.admit(sleep, clock)
            self.assertIsNone(resources.thread.ident)

    def test_admission_RAM_stability_and_time_budget_are_not_bypassed(self):
        resources = self.fixture([self.row(ram=5), self.row(ram=5)])
        sleep, clock = self.clock()
        self.assertEqual(resources.admit(sleep, clock), 2)
        self.assertEqual(clock(), 1)
        # 시작/중단이 같은 95% 상한이다. 초과하면 재시도 없이 즉시 중단한다.
        resources = self.fixture([self.row(ram=5), self.row(ram=4.99)])
        sleep, clock = self.clock()
        with self.assertRaisesRegex(ValueError, "^STOP_LOW_AVAILABLE_RAM$"):
            resources.admit(sleep, clock)
        self.assertEqual(len(resources.samples), 2)
        resources = self.fixture([self.row()]*2)
        slow_clock = Mock(side_effect=[0, 0, 0.5, 4])
        with self.assertRaisesRegex(ValueError, "^bootstrap_idle_window_not_admitted$"):
            resources.admit(Mock(), slow_clock)

    def test_runtime_four_CPU_samples_reset_and_sticky_stop(self):
        resources = self.fixture([self.row(cpu=98)]*3+[self.row(cpu=97)]+[self.row(cpu=98)]*4+[self.row()])
        for _ in range(7):
            resources.sample()
            self.assertFalse(resources.stop.is_set())
        resources.sample()
        self.assertEqual(resources.reason, "STOP_SUSTAINED_SYSTEM_CPU")
        resources.sample()
        self.assertTrue(resources.stop.is_set())
        self.assertEqual(resources.reason, "STOP_SUSTAINED_SYSTEM_CPU")

    def test_invalid_telemetry_observation_failure_and_sample_budget_latch(self):
        for row in (None, [], {}, {"system_cpu_percent": 1}):
            resources = self.fixture([row])
            with self.assertRaisesRegex(ValueError, "^STOP_RESOURCE_OBSERVATION_INVALID$"):
                resources.sample()
            self.assertTrue(resources.stop.is_set())
        for value in (math.nan, math.inf, -1, 101, True, "98"):
            resources = self.fixture([self.row(cpu=value)])
            with self.assertRaises(ValueError):
                resources.sample()
            self.assertTrue(resources.stop.is_set())
            self.assertEqual(resources.reason, "STOP_RESOURCE_OBSERVATION_FAILED")
        resources = self.fixture([OSError("not stored")])
        with self.assertRaises(OSError):
            resources.sample()
        self.assertTrue(resources.stop.is_set())
        resources = self.fixture([])
        resources.samples = [self.row()]*subject.MAX_SAMPLES
        with self.assertRaisesRegex(ValueError, "^STOP_RESOURCE_SAMPLE_BUDGET$"):
            resources.sample()
        resources.windows.sample.assert_not_called()

    def test_watch_failure_stop_and_lifecycle_no_real_thread(self):
        resources = self.fixture([self.row(commit=95)])
        resources.done.wait = Mock(return_value=False)
        resources.watch()
        self.assertEqual(resources.reason, "STOP_SYSTEM_COMMIT_PRESSURE")
        resources.done.wait.assert_called_once_with(0.5)
        resources = self.fixture([OSError("fixture")])
        resources.done.wait = Mock(return_value=False)
        resources.watch()
        self.assertTrue(resources.stop.is_set())
        resources = self.fixture([])
        resources.admit = Mock(return_value=2)
        resources.thread.start = Mock()
        resources.start()
        resources.admit.assert_called_once_with()
        resources.thread.start.assert_called_once_with()
        resources = self.fixture([])
        resources.done.set()
        sleep, clock = self.clock()
        with self.assertRaisesRegex(ValueError, "^sql_admission_lifecycle_invalid$"):
            resources.admit(sleep, clock)
        resources.windows.sample.assert_not_called()

    def test_policy_exact_limits_and_no_false_owned_or_container_qualification(self):
        policy = subject.resource_policy()
        self.assertEqual({key: policy[key] for key in ("container_memory_bytes", "container_swap_total_bytes", "pids_limit")},
            {"container_memory_bytes": 536870912, "container_swap_total_bytes": 536870912, "pids_limit": 64})
        self.assertEqual(policy["maximum_commit_used_percent"], 95)
        self.assertEqual(policy["minimum_available_ram_percent"], 5)
        self.assertEqual(policy["start_available_ram_min_percent"], 5)
        self.assertFalse(policy["host_child_aggregate_job_enforced"])
        self.assertFalse(policy["container_kernel_limits_qualified_by_this_helper"])
        self.assertNotIn("post_hash_idle_CPU_max_percent", policy)
        self.assertNotIn("post_hash_idle_RAM_min_mib", policy)


if __name__ == "__main__":
    unittest.main()
