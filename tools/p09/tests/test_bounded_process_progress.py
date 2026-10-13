"""Actual pipe tests and bounded synthetic chunks; not SQL/native acceptance."""
import io
import hashlib
import os
import subprocess
import sys
import time
from types import SimpleNamespace
import unittest

from bounded_process_progress import BoundedProcessCapture, LIMIT, MAX_INPUT, MAX_OUTPUT
from conservative_maintenance import Windows


class BoundedProcessProgressTests(unittest.TestCase):
    def child(self, code, input_text=None, output_limit=LIMIT, parse_markers=True):
        windows = Windows()
        job = windows.job()
        child = capture = None
        def cleanup():
            try:
                self.assertTrue(windows.k.TerminateJobObject(job, 1))
                if child is not None:
                    if child.poll() is None:
                        child.kill()
                    child.wait(timeout=2)
                    if capture is not None:
                        capture.close()
                    else:
                        for stream in (child.stdin, child.stdout, child.stderr):
                            stream.close()
                info = windows.accounting(job)
                self.assertEqual(info["active_processes"], 0)
                self.owned_job_observations = getattr(self, "owned_job_observations", []) + [info]
            finally:
                self.assertTrue(windows.k.CloseHandle(job))
        self.addCleanup(cleanup)
        self.assertTrue(windows.verify_job_limits(job)["verified"])
        launcher = "import sys;assert sys.stdin.readline()=='P149_PIPE_GO\\n';exec(sys.argv[1])"
        child = subprocess.Popen([sys.executable, "-c", launcher, code], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS,
            env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        handle = windows.k.OpenProcess(0x101, False, child.pid)
        try:
            self.assertTrue(handle and windows.k.AssignProcessToJobObject(job, handle))
        finally:
            if handle:
                self.assertTrue(windows.k.CloseHandle(handle))
        child.stdin.write("P149_PIPE_GO\n")
        child.stdin.flush()
        capture = BoundedProcessCapture(child, input_text=input_text, output_limit=output_limit,
            parse_markers=parse_markers)
        return child, capture

    @staticmethod
    def fixture(stdout=b"", stderr=b""):
        process = SimpleNamespace(stdin=io.BytesIO(), stdout=io.BufferedReader(io.BytesIO(stdout)),
            stderr=io.BufferedReader(io.BytesIO(stderr)), wait=lambda timeout: 0)
        capture = BoundedProcessCapture(process)
        capture.close()
        return capture

    def test_actual_marker_is_observed_before_child_exit(self):
        child, capture = self.child("import sys,time;sys.stderr.write('P146_STAGE:source_begin\\n');sys.stderr.flush();time.sleep(2)")
        deadline = time.monotonic() + 1.5
        markers = []
        while time.monotonic() < deadline and not markers:
            time.sleep(.02)
            markers, observations = capture.progress()
        self.assertEqual(markers, ["source_begin"])
        self.assertIsNone(child.poll())
        self.assertEqual(set(observations[0]), {"marker", "command_elapsed_seconds"})
        self.assertGreaterEqual(observations[0]["command_elapsed_seconds"], 0)

    def test_actual_final_JSON_and_stderr_are_preserved(self):
        child, capture = self.child("import sys;print('{\"state\":\"TEST_ONLY\"}');sys.stderr.write('P146_STAGE:consumer_begin\\n')")
        output, errors = capture.communicate(timeout=3)
        self.assertEqual(child.returncode, 0)
        self.assertEqual(output.strip(), '{"state":"TEST_ONLY"}')
        self.assertEqual(errors.strip(), "P146_STAGE:consumer_begin")

    def test_stdout_and_stderr_are_individually_bounded(self):
        for name in ("stdout", "stderr"):
            capture = self.fixture()
            capture._accept(name, b"x" * LIMIT)
            capture._accept(name, b"x")
            with self.assertRaisesRegex(ValueError, "^live_progress_output_limit$"):
                capture.progress()
            self.assertLessEqual(len(capture.buffers[name]), LIMIT)

    def test_split_CRLF_markers_preserve_order_without_duplicates(self):
        capture = self.fixture()
        for chunk in (b"P146_STA", b"GE:source_begin\r", b"\nP146_STAGE:consumer_begin\n"):
            capture._accept("stderr", chunk)
        self.assertEqual(capture.progress()[0], ["source_begin", "consumer_begin"])

    def test_unknown_or_malformed_marker_is_not_disclosed(self):
        for marker in (b"private_value", b"source_begin extra"):
            capture = self.fixture(stderr=b"P146_STAGE:" + marker + b"\n")
            with self.assertRaisesRegex(ValueError, "^live_progress_marker_scope$"):
                capture.progress()
            self.assertEqual(capture.markers, [])

    def test_incomplete_stage_marker_is_not_success(self):
        capture = self.fixture(stderr=b"P146_STAGE:source_begin")
        with self.assertRaisesRegex(ValueError, "^live_progress_marker_incomplete$"):
            capture.progress()

    def test_closed_pipes_do_not_make_live_child_complete(self):
        child, capture = self.child("import os,time;os.close(1);os.close(2);time.sleep(2)")
        started = time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired):
            capture.communicate(timeout=.1)
        self.assertGreaterEqual(time.monotonic() - started, .08)
        self.assertIsNone(child.poll())

    def test_non_marker_private_text_is_not_in_progress_metadata(self):
        capture = self.fixture(stderr=b"private_test_marker\nP146_STAGE:source_begin\n")
        markers, observations = capture.progress()
        self.assertEqual(markers, ["source_begin"])
        self.assertNotIn("private_test_marker", str(observations))

    def test_actual_bounded_input_and_output_progress_can_overlap(self):
        text = "한글\\\"\n" * 12000
        # The child fills stdout before reading stdin: sequential write/read deadlocks.
        code = "import sys,hashlib;sys.stdout.write('x'*65536);sys.stdout.flush();data=sys.stdin.read();sys.stdout.write(hashlib.sha256(data.encode()).hexdigest());sys.stderr.write('done')"
        child, capture = self.child(code, text, output_limit=MAX_OUTPUT, parse_markers=False)
        output, errors = capture.communicate(timeout=5)
        self.assertEqual(child.returncode, 0)
        # TextIOWrapper preserves Windows newline conversion from communicate(input=...).
        self.assertEqual(output, "x"*65536 + hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(errors, "done")
        self.assertEqual(capture.progress(), ([], []))

    def test_custom_limits_keep_full_bytes_and_never_truncate_success(self):
        capture = self.fixture()
        capture.output_limit, capture.parse_markers = 4, False
        capture._accept("stdout", b"abcd")
        self.assertEqual(bytes(capture.buffers["stdout"]), b"abcd")
        capture._accept("stdout", b"e")
        with self.assertRaisesRegex(ValueError, "^live_progress_output_limit$"):
            capture.progress()
        self.assertEqual(bytes(capture.buffers["stdout"]), b"abcd")

    def test_no_marker_mode_retains_stderr_without_interpreting_SQL_text(self):
        capture = self.fixture()
        capture.parse_markers = False
        capture._accept("stderr", b"P146_STAGE:private-value\n")
        self.assertEqual(capture.progress(), ([], []))
        self.assertEqual(capture.pending, b"")

    def test_input_byte_limit_encoding_and_option_scope_precede_threads(self):
        for text, reason in (("a"*(MAX_INPUT+1), "owned_pipe_input_limit"),
                ("한"*(MAX_INPUT//3+1), "owned_pipe_input_limit"),
                ("\ud800", "owned_pipe_input_encoding_failed")):
            process = SimpleNamespace(stdin=io.BytesIO())
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, "^"+reason+"$"):
                BoundedProcessCapture(process, input_text=text)
            self.assertFalse(process.stdin.closed)
        for options in ({"output_limit": 0}, {"output_limit": MAX_OUTPUT+1},
                {"output_limit": True}, {"parse_markers": "true"}, {"input_text": b"bytes"}):
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, "^owned_pipe_scope_invalid$"):
                BoundedProcessCapture(SimpleNamespace(), **options)

    def test_input_write_failures_are_closed_and_cannot_report_success(self):
        class RejectingInput(io.StringIO):
            def write(self, value):
                raise OSError("private-value-never-printed")
        process = SimpleNamespace(stdin=RejectingInput(), stdout=io.BufferedReader(io.BytesIO()),
            stderr=io.BufferedReader(io.BytesIO()), wait=lambda timeout: 0)
        capture = BoundedProcessCapture(process, input_text="fixture")
        capture.close()
        with self.assertRaisesRegex(ValueError, "^owned_pipe_input_write_failed$"):
            capture.communicate(timeout=1)
        self.assertTrue(process.stdin.closed)

    def test_empty_input_is_closed_without_becoming_no_input(self):
        class RecordingInput(io.StringIO):
            def close(self):
                self.saved = self.getvalue()
                super().close()
        process = SimpleNamespace(stdin=RecordingInput(), stdout=io.BufferedReader(io.BytesIO()),
            stderr=io.BufferedReader(io.BytesIO()), wait=lambda timeout: 0)
        capture = BoundedProcessCapture(process, input_text="")
        capture.close()
        self.assertEqual(capture.communicate(timeout=1), ("", ""))
        self.assertEqual(process.stdin.saved, "")


if __name__ == "__main__":
    unittest.main()
