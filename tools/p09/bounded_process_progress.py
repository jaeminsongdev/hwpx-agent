"""Bounded in-memory pipe capture; no raw log files or private subprocess internals."""
import re
import math
import io
import os
import subprocess
import threading
import time


LIMIT = 32768
MAX_INPUT = 1024 * 1024
MAX_OUTPUT = 1024 * 1024
ALLOWED_MARKERS = frozenset({"source_begin", "consumer_begin", "live_begin", "connect_first_begin",
    "connect_second_begin", "stale_CAS_begin", "race_begin", "race_joined", "denied_callback_begin"})


class BoundedProcessCapture:
    def __init__(self, process, input_text=None, output_limit=LIMIT, parse_markers=True):
        if not isinstance(output_limit, int) or isinstance(output_limit, bool) or not 1 <= output_limit <= MAX_OUTPUT \
                or not isinstance(parse_markers, bool) or (input_text is not None and not isinstance(input_text, str)):
            raise ValueError("owned_pipe_scope_invalid")
        if input_text is not None:
            if len(input_text) > MAX_INPUT:
                raise ValueError("owned_pipe_input_limit")
            try:
                size = 0
                for start in range(0, len(input_text), 2048):
                    chunk = input_text[start:start+2048]
                    size += len(chunk.encode("utf-8"))
                    if isinstance(process.stdin, io.TextIOBase):
                        size += chunk.count("\n") * (len(os.linesep)-1)
                    if size > MAX_INPUT:
                        raise ValueError("owned_pipe_input_limit")
            except UnicodeError:
                raise ValueError("owned_pipe_input_encoding_failed") from None
        self.process = process
        self.output_limit, self.parse_markers = output_limit, parse_markers
        self.started = time.monotonic()
        self.lock = threading.Lock()
        self.buffers = {"stdout": bytearray(), "stderr": bytearray()}
        self.pending = bytearray()
        self.markers, self.observations = [], []
        self.error = None
        self.threads = []
        # Readers start before input transmission, so a child can emit while reading.
        # None preserves the original Rust-probe EOF behavior.
        if input_text is None:
            process.stdin.close()
        for name in ("stdout", "stderr"):
            stream = getattr(process, name)
            thread = threading.Thread(target=self._read, args=(name, stream), daemon=True)
            self.threads.append(thread)
            thread.start()
        if input_text is not None:
            thread = threading.Thread(target=self._write, args=(process.stdin, input_text), daemon=True)
            self.threads.append(thread)
            thread.start()

    def _write(self, stream, text):
        try:
            for start in range(0, len(text), 2048):
                with self.lock:
                    if self.error:
                        return
                chunk = text[start:start+2048]
                # Preserve TextIOWrapper's UTF-8/newline behavior from communicate(input=...).
                payload = chunk if isinstance(stream, io.TextIOBase) else chunk.encode("utf-8")
                if stream.write(payload) != len(payload):
                    raise ValueError("owned_pipe_input_short_write")
            stream.flush()
        except (OSError, ValueError):
            with self.lock:
                self.error = self.error or "owned_pipe_input_write_failed"
        finally:
            try:
                stream.close()
            except (OSError, ValueError):
                with self.lock:
                    self.error = self.error or "owned_pipe_input_close_failed"

    def _accept(self, name, chunk):
        with self.lock:
            if self.error:
                return
            if len(self.buffers[name]) + len(chunk) > self.output_limit:
                self.error = "live_progress_output_limit"
                return
            self.buffers[name].extend(chunk)
            if name != "stderr" or not self.parse_markers:
                return
            self.pending.extend(chunk)
            while b"\n" in self.pending:
                line, _, tail = self.pending.partition(b"\n")
                self.pending = bytearray(tail)
                if not line.startswith(b"P146_STAGE:"):
                    continue
                match = re.fullmatch(rb"P146_STAGE:([A-Za-z0-9_]+)\r?", line)
                marker = match[1].decode("ascii") if match else None
                if marker not in ALLOWED_MARKERS:
                    self.error = "live_progress_marker_scope"
                    return
                self.markers.append(marker)
                self.observations.append({"marker": marker,
                    "command_elapsed_seconds": round(time.monotonic() - self.started, 3)})

    def _read(self, name, stream):
        try:
            # read1 returns available bytes without waiting for EOF or a full buffer.
            reader = getattr(stream, "buffer", stream)
            while chunk := reader.read1(4096):
                self._accept(name, chunk)
            if name == "stderr" and self.parse_markers:
                with self.lock:
                    if self.pending.startswith(b"P146_STAGE:"):
                        self.error = self.error or "live_progress_marker_incomplete"
        except (OSError, ValueError):
            with self.lock:
                self.error = self.error or "owned_pipe_read_failed"
        finally:
            stream.close()

    def progress(self):
        with self.lock:
            if self.error:
                raise ValueError(self.error)
            return list(self.markers), [dict(row) for row in self.observations]

    def communicate(self, timeout):
        deadline = time.monotonic() + timeout
        self.process.wait(timeout=timeout)
        for thread in self.threads:
            thread.join(max(0, deadline - time.monotonic()))
        if any(thread.is_alive() for thread in self.threads):
            raise subprocess.TimeoutExpired("owned_probe", timeout)
        self.progress()
        with self.lock:
            return tuple(bytes(self.buffers[name]).decode("utf-8", errors="replace")
                for name in ("stdout", "stderr"))

    def close(self):
        for thread in self.threads:
            thread.join(2)
        if any(thread.is_alive() for thread in self.threads):
            raise ValueError("owned_pipe_cleanup_timeout")


def bounded_observation_run(args, *, cwd, timeout=3, creationflags=0, process_factory=None):
    """Bounded EOF capture for the drivers' existing read-only wait metadata command."""
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) \
            or not math.isfinite(timeout) or not 0 < timeout <= 3:
        raise ValueError("owned_observation_scope_invalid")
    factory = subprocess.Popen if process_factory is None else process_factory
    process = factory(args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", creationflags=creationflags)
    capture = None
    try:
        capture = BoundedProcessCapture(process, output_limit=16384, parse_markers=False)
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired("owned_wait_observation", timeout)
            try:
                output, errors = capture.communicate(timeout=min(.25, remaining))
                if process_factory is not None:
                    process.observe()
                # Match subprocess.run(text=True)'s universal newline decoding.
                output = output.replace("\r\n", "\n").replace("\r", "\n")
                errors = errors.replace("\r\n", "\n").replace("\r", "\n")
                return subprocess.CompletedProcess(args, process.returncode, output, errors)
            except subprocess.TimeoutExpired:
                capture.progress()
                if process_factory is not None:
                    process.observe()
    finally:
        try:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=2)
        finally:
            try:
                if capture is not None:
                    capture.close()
                else:
                    for stream in (process.stdin, process.stdout, process.stderr):
                        stream.close()
            finally:
                if process_factory is not None:
                    process.close()
