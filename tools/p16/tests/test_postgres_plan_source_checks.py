from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "run_postgres_plan_source_checks.py"
SPEC = importlib.util.spec_from_file_location("p16_postgres_plan_source_checks", SOURCE)
assert SPEC is not None and SPEC.loader is not None
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


def state(port="54321", ip="127.0.0.1", owner="owned"):
    return {"Config": {"Labels": {checks.LABEL: owner}},
            "NetworkSettings": {"Ports": {"5432/tcp": [{"HostIp": ip, "HostPort": port}]}}}


class PostgresPlanSourceHarnessTests(unittest.TestCase):
    def test_harness_rebuilds_the_locked_probe_before_acceptance(self):
        source = SOURCE.read_text(encoding="utf-8")
        build = 'invoke([cargo, "build", "--locked", "-p", "mcp-control-plane", "--example",'
        self.assertIn(build, source)
        self.assertLess(source.index(build), source.index("require(probe.is_file()"))

    def test_migration_contract_is_transactional_immutable_and_receipt_bound(self):
        up = (checks.ROOT / "migrations/postgres/0011_p16_plan_source.up.sql").read_text(
            encoding="utf-8")
        down = (checks.ROOT / "migrations/postgres/0011_p16_plan_source.down.sql").read_text(
            encoding="utf-8")
        self.assertTrue(up.startswith("BEGIN;\n") and up.rstrip().endswith("COMMIT;"))
        self.assertTrue(down.startswith("BEGIN;\n") and down.rstrip().endswith("COMMIT;"))
        for required in (
            "CREATE TABLE hwpx_agent.revision_graph_bindings",
            "receipt.commit_id = seal.commit_id",
            "receipt.subject_sha256 = NEW.created_by_subject_sha256",
            "revision.created_by_subject_sha256 = NEW.created_by_subject_sha256",
            "CREATE TRIGGER revision_graph_bindings_immutable",
            "FORCE ROW LEVEL SECURITY",
            "'p16.plan_source_v1'",
        ):
            self.assertIn(required, up)
        for required in (
            "hwpx_agent.allow_p16_plan_source_rollback",
            "IF EXISTS (SELECT 1 FROM hwpx_agent.revision_graph_bindings)",
            "EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 11)",
        ):
            self.assertIn(required, down)
        self.assertNotRegex(up + down, r"(?m)^\s*\\")

    def test_current_endpoint_requires_exact_owner_and_loopback(self):
        self.assertEqual(checks.loopback_port(state(), "owned"), "54321")
        for current in (state(owner="other"), state(ip="0.0.0.0"), state(ip="::1"), {}):
            with self.subTest(current=current), self.assertRaises(checks.CheckFailure):
                checks.loopback_port(current, "owned")

    def test_endpoint_rejects_invalid_and_ambiguous_bindings(self):
        for port in (None, 54321, "", "0", "65536", "00080", "5432;payload", "-1", "１２"):
            with self.subTest(port=port), self.assertRaises(checks.CheckFailure):
                checks.loopback_port(state(port), "owned")
        current = state()
        current["NetworkSettings"]["Ports"]["5432/tcp"] = [
            {"HostIp": "127.0.0.1", "HostPort": "1"},
            {"HostIp": "127.0.0.1", "HostPort": "2"},
        ]
        with self.assertRaises(checks.CheckFailure):
            checks.loopback_port(current, "owned")

    def test_child_failure_summary_is_closed(self):
        private = "private-database-diagnostic"
        result = subprocess.CompletedProcess([], 1, private, "\n".join([
            private,
            "P16_POSTGRES_PLAN_SOURCE_CONNECT_FAILED stage=POLICIES",
            "P16_POSTGRES_PLAN_SOURCE_PROBE_FAILED code=ACCESS_DENIED",
        ]))
        with patch.object(checks.subprocess, "run", return_value=result):
            with self.assertRaises(checks.CheckFailure) as caught:
                checks.invoke(["synthetic-command"])
        self.assertEqual(str(caught.exception),
                         "child_failed exit=1 code=ACCESS_DENIED connect_stage=POLICIES")
        self.assertNotIn(private, str(caught.exception))

    def test_unrecognized_child_diagnostics_are_not_forwarded(self):
        result = subprocess.CompletedProcess([], 1, "", "\n".join([
            "P16_POSTGRES_PLAN_SOURCE_CONNECT_FAILED stage=PRIVATE",
            "P16_POSTGRES_PLAN_SOURCE_PROBE_FAILED code=PRIVATE",
        ]))
        with patch.object(checks.subprocess, "run", return_value=result):
            with self.assertRaises(checks.CheckFailure) as caught:
                checks.invoke(["synthetic-command"])
        self.assertEqual(str(caught.exception), "child_failed exit=1")


if __name__ == "__main__":
    unittest.main()
