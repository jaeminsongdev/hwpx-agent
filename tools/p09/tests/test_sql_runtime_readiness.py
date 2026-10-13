"""ServerVersion readiness/timeout contracts; no Docker or file writes."""
import io
import json
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

import qualify_sql_runtime_environment as subject


class SQLRuntimeReadinessTests(unittest.TestCase):
    def result(self, *, code=0, output='{"version":"28.5.1","os":"linux"}', error=""):
        return SimpleNamespace(returncode=code, stdout=output, stderr=error)

    def test_two_commands_use_server_os_not_client_os_or_info(self):
        rows = subject.commands("C:/fixture/docker.exe")
        self.assertEqual([kind for kind, _ in rows], ["server", "image"])
        self.assertIn(".Server.Os", rows[0][1][-1])
        self.assertNotIn(".Client", rows[0][1][-1])
        self.assertNotIn("info", rows[0][1])
        self.assertEqual(rows[0][1][1:3], ["--host", subject.HOST])

    def test_server_version_and_linux_are_both_required(self):
        self.assertIs(subject.observation(self.result(), "server"), True)
        for output in ('{"version":"28.5.1","os":"windows"}', '{"version":"bad","os":"linux"}',
                '{"version":"28.5.1"}', '{"version":true,"os":"linux"}'):
            with self.assertRaises(ValueError):
                subject.observation(self.result(output=output), "server")

    def test_extra_duplicate_and_non_json_server_output_rejected(self):
        for output in ('{"version":"28.5.1","os":"linux","secret":"PRIVATE_FIXTURE"}',
                '{"version":"28.5.1","os":"linux","os":"linux"}', "PRIVATE_FIXTURE"):
            with self.assertRaises(ValueError):
                subject.observation(self.result(output=output), "server")

    def test_image_missing_and_shape_failures_are_not_readiness_success(self):
        self.assertEqual(subject.observation(self.result(output='"sha256:'+'a'*64+'"'), "image"), "sha256:"+"a"*64)
        with self.assertRaisesRegex(ValueError, "SQL_ENVIRONMENT_FIXED_IMAGE_MISSING"):
            subject.observation(self.result(code=1, output="", error="Error: No such image: fixed"), "image")
        for result in (self.result(code=True), self.result(error="x"*16385), self.result(output='"invalid"')):
            with self.assertRaises(ValueError):
                subject.observation(result, "image")

    def mocked_main(self, *, timeout=False, server_error=False):
        sink = io.StringIO()
        class Output:
            def __enter__(self):
                return sink
            def __exit__(self, *args):
                return False
        resources = SimpleNamespace(admit=Mock(), start=Mock(), windows=object(), samples=[], reason=None,
            checkpoint_io=Mock())
        reader = SimpleNamespace(pin=lambda name: {"path": name, "bytes": 1, "sha256": "0"*64},
            finish=Mock(), finished=False, summary=lambda: {"fixture": True})
        profile = {"cleanup_confirmed": True, "owned_tree_empty": True, "job_handle_closed": True}
        def observed(arguments, **kwargs):
            kwargs["process_factory"](arguments, cwd=subject.c.ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            if "version" in arguments:
                if server_error:
                    return self.result(code=1, output="", error="unavailable")
                return self.result()
            if timeout:
                raise subprocess.TimeoutExpired("owned_wait_observation", 3)
            return self.result(code=1, output="", error="Error: No such image: fixed")
        def finished(resource, row):
            row["resource_watcher_cleanup_confirmed"] = True
        with patch.object(sys, "argv", ["qualifier", "--run", "98"]), \
                patch.object(subject, "SQLRuntimeResources", return_value=resources), \
                patch.object(subject, "LiveSQLReader", return_value=reader), \
                patch.object(subject, "OwnedSQLJobProcess", return_value=SimpleNamespace(profile=profile)), \
                patch.object(subject, "bounded_observation_run", side_effect=observed), \
                patch.object(subject, "finish_watcher", side_effect=finished), \
                patch.object(subject.shutil, "which", return_value="C:/fixture/docker.exe"), \
                patch.object(Path, "exists", return_value=False), patch.object(Path, "is_file", return_value=True), \
                patch.object(Path, "open", return_value=Output()), patch("sys.stdout", new=io.StringIO()):
            code = subject.main()
        return code, json.loads(sink.getvalue())

    def test_timed_out_image_query_does_not_retain_previous_exit_zero(self):
        code, row = self.mocked_main(timeout=True)
        self.assertNotEqual(code, 0)
        self.assertEqual(row["image_presence_state"], "UNKNOWN")
        self.assertEqual(row["last_query_kind"], "image")
        self.assertIsNone(row["last_query_exit_code"])
        self.assertEqual(row["query_observations"][-1]["outcome"], "TIMED_OUT")
        self.assertEqual(row["error_code"], "SQL_ENVIRONMENT_QUERY_TIMEOUT")

    def test_failed_server_keeps_image_not_queried_and_missing_is_distinct(self):
        _, row = self.mocked_main(server_error=True)
        self.assertEqual(row["image_presence_state"], "NOT_QUERIED")
        self.assertEqual(len(row["query_observations"]), 1)
        _, row = self.mocked_main()
        self.assertEqual(row["image_presence_state"], "MISSING")
        self.assertEqual(row["query_observations"][-1]["outcome"], "MISSING")
