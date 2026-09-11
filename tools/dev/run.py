"""Run a development command with live output and bounded redacted JSONL logs."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import BinaryIO, TextIO
import uuid


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_ROOT = ROOT / "tmp" / "dev-runs"
RUN_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
SENSITIVE_ASSIGNMENT = re.compile(
    r"(?i)\b(authorization|password|passwd|secret|token|api[-_]?key)"
    r"(\s*[:=]\s*)([^\s,;]+)"
)
SENSITIVE_JSON = re.compile(
    r'''(?i)(["'](?:authorization|password|passwd|secret|token|api[-_]?key)["']'''
    r'''\s*:\s*["'])([^"']*)(["'])'''
)
BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
URI_CREDENTIALS = re.compile(r"(?i)([a-z][a-z0-9+.-]*://)[^/@\s:]+:[^/@\s]+@")
MAX_ARGUMENTS = 128
MAX_ARGUMENT_CHARS = 4096
MAX_STREAM_CHUNK_BYTES = 16_384
MAX_QUEUED_STREAM_CHUNKS = 256


class DevRunError(ValueError):
    """Fail-closed configuration or runtime error with a bounded code."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise DevRunError(code)


def validate_name(name: str) -> str:
    _require(isinstance(name, str) and RUN_NAME.fullmatch(name) is not None, "run.name")
    return name


def validate_command(command: list[str]) -> list[str]:
    _require(0 < len(command) <= MAX_ARGUMENTS, "run.command")
    for argument in command:
        _require(
            isinstance(argument, str)
            and 0 < len(argument) <= MAX_ARGUMENT_CHARS
            and "\0" not in argument,
            "run.command",
        )
    return command


def redact(text: str, workspace: Path = ROOT) -> str:
    """Remove common credentials and the absolute workspace from persisted output."""
    redacted = text
    for spelling in (str(workspace), str(workspace).replace("\\", "/")):
        redacted = re.sub(re.escape(spelling), "<workspace>", redacted, flags=re.IGNORECASE)
    redacted = URI_CREDENTIALS.sub(r"\1<redacted>@", redacted)
    redacted = BEARER.sub("Bearer <redacted>", redacted)
    redacted = SENSITIVE_JSON.sub(r"\1<redacted>\3", redacted)
    return SENSITIVE_ASSIGNMENT.sub(r"\1\2<redacted>", redacted)


def _atomic_json(path: Path, value: dict[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".partial")
    raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    temporary.write_text(raw + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, path)


class BoundedJournal:
    def __init__(
        self,
        directory: Path,
        *,
        run_id: str,
        max_log_bytes: int,
        max_event_bytes: int,
    ) -> None:
        _require(1_048_576 <= max_log_bytes <= 268_435_456, "log.limit")
        _require(4_096 <= max_event_bytes <= 65_536, "event.limit")
        directory.mkdir(parents=True, exist_ok=False)
        self.directory = directory
        self.events_path = directory / "events.jsonl"
        self.summary_path = directory / "summary.json"
        self._stream = self.events_path.open("x", encoding="utf-8", newline="\n")
        self._run_id = run_id
        self._max_log_bytes = max_log_bytes
        self._max_event_bytes = max_event_bytes
        self._written = 0
        self._sequence = 0
        self._truncated = False

    def __repr__(self) -> str:
        return (
            "BoundedJournal("
            f"sequence={self._sequence}, written_bytes={self._written}, "
            f"truncated={self._truncated})"
        )

    @property
    def truncated(self) -> bool:
        return self._truncated

    def emit(self, event: str, elapsed_ms: int, **fields: object) -> None:
        _require(RUN_NAME.fullmatch(event) is not None, "event.type")
        if self._truncated and event in ("output", "heartbeat"):
            return
        self._sequence += 1
        document: dict[str, object] = {
            "schema": "hwpx-agent.dev-run-event/v1",
            "run_id": self._run_id,
            "sequence": self._sequence,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "elapsed_ms": elapsed_ms,
            "event": event,
            **fields,
        }
        encoded = self._encode_bounded(document)
        if self._written + len(encoded) > self._max_log_bytes:
            self._truncated = True
            return
        self._stream.write(encoded.decode("utf-8"))
        self._stream.flush()
        self._written += len(encoded)

    def _encode_bounded(self, document: dict[str, object]) -> bytes:
        encoded = (
            json.dumps(document, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        if len(encoded) <= self._max_event_bytes:
            return encoded
        message = document.get("message")
        _require(isinstance(message, str), "event.size")
        document["message"] = message[: max(0, (self._max_event_bytes - 1_024) // 6)]
        document["message_truncated"] = True
        encoded = (
            json.dumps(document, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        _require(len(encoded) <= self._max_event_bytes, "event.size")
        return encoded

    def finish(self, summary: dict[str, object]) -> None:
        self._stream.close()
        _atomic_json(self.summary_path, summary)


@dataclass(frozen=True)
class PreparedEnvironment:
    values: dict[str, str]
    sccache: str


def prepare_environment(command: list[str], *, use_sccache: bool) -> PreparedEnvironment:
    environment = os.environ.copy()
    executable = Path(command[0]).name.lower()
    if executable not in ("cargo", "cargo.exe") or not use_sccache:
        return PreparedEnvironment(environment, "disabled")
    if environment.get("RUSTC_WRAPPER"):
        return PreparedEnvironment(environment, "existing")
    if shutil.which("sccache") is None:
        return PreparedEnvironment(environment, "unavailable")
    environment["RUSTC_WRAPPER"] = "sccache"
    environment["CARGO_INCREMENTAL"] = "0"
    return PreparedEnvironment(environment, "enabled")


@dataclass(frozen=True)
class RunResult:
    run_id: str
    directory: Path
    status: str
    exit_code: int
    elapsed_ms: int
    log_truncated: bool
    sccache: str


def _pump(
    stream: BinaryIO,
    name: str,
    messages: queue.Queue[tuple[str, bytes] | None],
) -> None:
    try:
        while True:
            chunk = stream.readline(MAX_STREAM_CHUNK_BYTES)
            if not chunk:
                break
            messages.put((name, chunk))
    finally:
        messages.put(None)


def _console(stream: str) -> TextIO:
    return sys.stderr if stream == "stderr" else sys.stdout


def execute(
    command: list[str],
    *,
    name: str,
    log_root: Path = DEFAULT_LOG_ROOT,
    heartbeat_seconds: float = 5.0,
    max_log_bytes: int = 64 * 1024 * 1024,
    max_event_bytes: int = 32 * 1024,
    use_sccache: bool = False,
) -> RunResult:
    command = validate_command(command)
    name = validate_name(name)
    _require(1.0 <= heartbeat_seconds <= 60.0, "heartbeat.limit")
    run_id = uuid.uuid4().hex
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = log_root / f"{timestamp}-{name}-{run_id[:8]}"
    journal = BoundedJournal(
        directory,
        run_id=run_id,
        max_log_bytes=max_log_bytes,
        max_event_bytes=max_event_bytes,
    )
    prepared = prepare_environment(command, use_sccache=use_sccache)
    started = time.monotonic()
    journal.emit(
        "start",
        0,
        name=name,
        executable=Path(command[0]).name,
        argument_count=len(command) - 1,
        sccache=prepared.sccache,
    )
    _atomic_json(
        journal.summary_path,
        {
            "schema": "hwpx-agent.dev-run-summary/v1",
            "run_id": run_id,
            "name": name,
            "status": "running",
            "exit_code": None,
            "elapsed_ms": 0,
            "log_truncated": journal.truncated,
            "sccache": prepared.sccache,
        },
    )
    print(f"[dev-run] {name} started; live log: {journal.events_path}", flush=True)
    try:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=prepared.values,
            bufsize=0,
        )
    except OSError:
        elapsed_ms = round((time.monotonic() - started) * 1000)
        summary = {
            "schema": "hwpx-agent.dev-run-summary/v1",
            "run_id": run_id,
            "name": name,
            "status": "start_failed",
            "exit_code": 127,
            "elapsed_ms": elapsed_ms,
            "log_truncated": journal.truncated,
            "sccache": prepared.sccache,
        }
        journal.emit("end", elapsed_ms, status="start_failed", exit_code=127)
        journal.finish(summary)
        return RunResult(
            run_id, directory, "start_failed", 127, elapsed_ms, journal.truncated, prepared.sccache
        )
    _require(process.stdout is not None and process.stderr is not None, "run.pipe")
    messages: queue.Queue[tuple[str, bytes] | None] = queue.Queue(
        maxsize=MAX_QUEUED_STREAM_CHUNKS
    )
    threads = [
        threading.Thread(target=_pump, args=(process.stdout, "stdout", messages), daemon=True),
        threading.Thread(target=_pump, args=(process.stderr, "stderr", messages), daemon=True),
    ]
    for thread in threads:
        thread.start()
    completed_streams = 0
    next_heartbeat = started + heartbeat_seconds
    interrupted = False
    try:
        while completed_streams < 2 or process.poll() is None:
            now = time.monotonic()
            wait = max(0.0, min(0.25, next_heartbeat - now))
            try:
                message = messages.get(timeout=wait)
            except queue.Empty:
                message = "empty"
            if message is None:
                completed_streams += 1
            elif message != "empty":
                stream, raw = message
                decoded = raw.decode("utf-8", errors="replace")
                output = _console(stream)
                output.write(decoded)
                output.flush()
                elapsed_ms = round((time.monotonic() - started) * 1000)
                journal.emit(
                    "output",
                    elapsed_ms,
                    stream=stream,
                    message=redact(decoded.rstrip("\r\n")),
                )
            now = time.monotonic()
            if now >= next_heartbeat and process.poll() is None:
                elapsed_ms = round((now - started) * 1000)
                journal.emit("heartbeat", elapsed_ms, child_running=True)
                print(f"[dev-run] {name}: {elapsed_ms / 1000:.1f}s elapsed", flush=True)
                next_heartbeat = now + heartbeat_seconds
    except KeyboardInterrupt:
        interrupted = True
        process.terminate()
    if interrupted:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    exit_code = process.wait()
    for thread in threads:
        thread.join(timeout=1)
    elapsed_ms = round((time.monotonic() - started) * 1000)
    status = "interrupted" if interrupted else ("passed" if exit_code == 0 else "failed")
    reported_exit = 130 if interrupted else exit_code
    journal.emit("end", elapsed_ms, status=status, exit_code=reported_exit)
    summary = {
        "schema": "hwpx-agent.dev-run-summary/v1",
        "run_id": run_id,
        "name": name,
        "status": status,
        "exit_code": reported_exit,
        "elapsed_ms": elapsed_ms,
        "log_truncated": journal.truncated,
        "sccache": prepared.sccache,
    }
    journal.finish(summary)
    print(f"[dev-run] {name} {status} in {elapsed_ms / 1000:.1f}s", flush=True)
    return RunResult(
        run_id,
        directory,
        status,
        reported_exit,
        elapsed_ms,
        journal.truncated,
        prepared.sccache,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stream a command and persist bounded redacted development telemetry."
    )
    parser.add_argument("--name", required=True)
    parser.add_argument("--heartbeat-seconds", type=float, default=5.0)
    parser.add_argument("--max-log-mib", type=int, default=64)
    parser.add_argument("--sccache", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    command = arguments.command
    if command and command[0] == "--":
        command = command[1:]
    result = execute(
        command,
        name=arguments.name,
        heartbeat_seconds=arguments.heartbeat_seconds,
        max_log_bytes=arguments.max_log_mib * 1024 * 1024,
        use_sccache=arguments.sccache,
    )
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
