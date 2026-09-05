from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "run_postgres_artifact_checks.py"
SPEC = importlib.util.spec_from_file_location("p16_postgres_artifact_checks", SOURCE)
assert SPEC is not None and SPEC.loader is not None
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


def state(port="54321", ip="127.0.0.1", owner="owned"):
    return {"Config": {"Labels": {checks.LABEL: owner}},
            "NetworkSettings": {"Ports": {"5432/tcp": [{"HostIp": ip, "HostPort": port}]}}}


class PostgresArtifactHarnessTests(unittest.TestCase):
    def test_current_ephemeral_endpoint_is_not_cached(self):
        self.assertEqual(checks.loopback_port(state("54321"), "owned"), "54321")
        self.assertEqual(checks.loopback_port(state("54322"), "owned"), "54322")

    def test_endpoint_requires_exact_owned_container_and_loopback(self):
        for current in (state(owner="different"), state(ip="0.0.0.0"), state(ip="::1"), {}):
            with self.subTest(current=current), self.assertRaises(checks.CheckFailure):
                checks.loopback_port(current, "owned")

    def test_endpoint_rejects_invalid_and_ambiguous_bindings(self):
        for port in (None, 54321, "", "0", "65536", "00080", "5432;payload", "-1", "１２"):
            with self.subTest(port=port), self.assertRaises(checks.CheckFailure):
                checks.loopback_port(state(port), "owned")
        for bindings in ([], None, {}, [{"HostIp": "127.0.0.1", "HostPort": "1"}] * 2):
            current = state()
            current["NetworkSettings"]["Ports"]["5432/tcp"] = bindings
            with self.subTest(bindings=bindings), self.assertRaises(checks.CheckFailure):
                checks.loopback_port(current, "owned")

    def test_failure_summary_contains_only_closed_stages_and_public_category(self):
        private = "private-database-credential-and-sql-sentinel"
        result = subprocess.CompletedProcess([], 1, private, "\n".join([
            private,
            "P16_POSTGRES_ARTIFACT_PROBE_STAGE stage=CONNECT",
            "P16_POSTGRES_ARTIFACT_CONNECT_FAILED stage=TRANSPORT",
            "P16_POSTGRES_ARTIFACT_PROBE_FAILED code=STORAGE_FAILURE",
        ]))
        with patch.object(checks.subprocess, "run", return_value=result):
            with self.assertRaises(checks.CheckFailure) as caught:
                checks.invoke(["synthetic-command"])
        self.assertEqual(str(caught.exception),
                         "child_failed exit=1 code=STORAGE_FAILURE probe_stage=CONNECT connect_stage=TRANSPORT")
        self.assertNotIn(private, str(caught.exception))

    def test_unrecognized_diagnostic_stages_are_not_emitted(self):
        result = subprocess.CompletedProcess([], 1, "", "\n".join([
            "P16_POSTGRES_ARTIFACT_PROBE_STAGE stage=PRIVATE",
            "P16_POSTGRES_ARTIFACT_CONNECT_FAILED stage=PRIVATE",
        ]))
        with patch.object(checks.subprocess, "run", return_value=result):
            with self.assertRaises(checks.CheckFailure) as caught:
                checks.invoke(["synthetic-command"])
        self.assertEqual(str(caught.exception), "child_failed exit=1")


if __name__ == "__main__":
    unittest.main()
