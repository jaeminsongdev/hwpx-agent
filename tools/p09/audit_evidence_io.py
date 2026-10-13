"""Per-audit byte binding; no cross-run/raw/parsed JSON cache or subprocesses.

Hash-only files use 64 KiB chunks. JSON/text must be parsed in full, with an
explicit 16 MiB per-input allocation budget; oversize means failure, never skip.
The closing fresh-hash pass is required and is not replaced by the local pins.
"""
import hashlib
import json
import math
from pathlib import Path
import time

CHUNK_BYTES = 64 * 1024
MAX_PARSE_BYTES = 16 * 1024 * 1024
READ_BYTES_PER_SECOND = 8 * 1024 * 1024


def require(ok, code):
    if not ok:
        raise ValueError(code)


class AuditReadPacer:
    """One chunk of burst credit; idle/parse time cannot accumulate a large IO burst."""
    def __init__(self, clock=time.monotonic, sleeper=time.sleep):
        self.clock, self.sleeper = clock, sleeper
        self.tokens = CHUNK_BYTES
        self.last = self.clock()
        require(type(self.last) in (int, float) and math.isfinite(self.last), "audit_io_clock_invalid")
        self.bytes_paced = 0
        self.requested_sleep_seconds = 0.0

    def reserve(self, checkpoint):
        attempts = 0
        while True:
            now = self.clock()
            require(type(now) in (int, float) and math.isfinite(now) and now >= self.last,
                "audit_io_clock_invalid")
            self.tokens = min(CHUNK_BYTES, self.tokens + (now-self.last)*READ_BYTES_PER_SECOND)
            self.last = now
            if self.tokens >= CHUNK_BYTES:
                self.tokens -= CHUNK_BYTES
                return
            attempts += 1
            require(attempts <= 64, "audit_io_clock_not_advancing")
            delay = min(0.05, max(0.000001, (CHUNK_BYTES-self.tokens)/READ_BYTES_PER_SECOND))
            checkpoint()
            self.sleeper(delay)
            self.requested_sleep_seconds += delay
            checkpoint()

    def refund(self, actual_bytes):
        require(type(actual_bytes) is int and 0 <= actual_bytes <= CHUNK_BYTES, "audit_io_charge_invalid")
        self.bytes_paced += actual_bytes
        self.tokens = min(CHUNK_BYTES, self.tokens + CHUNK_BYTES-actual_bytes)


class AuditEvidenceReader:
    def __init__(self, root, checkpoint, maximum_parse_bytes=MAX_PARSE_BYTES):
        require(type(maximum_parse_bytes) is int and maximum_parse_bytes > 0,
            "audit_parse_budget_invalid")
        self.root, self.checkpoint = Path(root), checkpoint
        self.maximum_parse_bytes = maximum_parse_bytes
        self.snapshots = {}
        self.read_passes = self.bytes_read = self.final_fresh_hashes = 0
        self.pacer = AuditReadPacer()

    def _source(self, name):
        # Same direct-file/link checks as the original SQL pin implementation.
        source = self.root / name
        require(source.is_file() and not source.is_symlink() and not source.is_junction(),
            "sql_source_link_or_missing")
        return source

    def _read(self, name, parse=False):
        self.checkpoint()
        digest, size = hashlib.sha256(), 0
        buffer = bytearray() if parse else None
        with self._source(name).open("rb") as stream:
            self.read_passes += 1
            while True:
                # Reserve BEFORE disk read, refund short reads/EOF, share across files and final hash.
                self.pacer.reserve(self.checkpoint)
                chunk = stream.read(CHUNK_BYTES)
                self.pacer.refund(len(chunk))
                if not chunk:
                    break
                self.checkpoint()
                size += len(chunk)
                self.bytes_read += len(chunk)
                if parse:
                    require(size <= self.maximum_parse_bytes, "audit_parse_budget_exceeded")
                    buffer.extend(chunk)
                digest.update(chunk)
        self.checkpoint()
        return {"path": name, "bytes": size, "sha256": digest.hexdigest()}, buffer

    def _bind(self, name, actual):
        previous = self.snapshots.get(name)
        require(previous is None or actual == previous, "input_changed_during_audit")
        if previous is None:
            self.snapshots[name] = actual
        return self.snapshots[name]

    def pin(self, name):
        self.checkpoint()
        if name not in self.snapshots:
            actual, _ = self._read(name)
            self._bind(name, actual)
        return self.snapshots[name]

    def json(self, name):
        actual, buffer = self._read(name, parse=True)
        self._bind(name, actual)
        try:
            return json.loads(buffer.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("audit_json_invalid") from None

    def fresh_pin(self, name):
        # Live executables/source require every original repeated check to read all bytes.
        actual, _ = self._read(name)
        return self._bind(name, actual)

    def text(self, name):
        actual, buffer = self._read(name, parse=True)
        self._bind(name, actual)
        try:
            # Match Path.read_text(encoding="utf-8") universal-newline semantics.
            return buffer.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        except UnicodeDecodeError:
            raise ValueError("audit_text_invalid") from None

    def finish(self):
        # Read every byte again; never promote the first pin into final freshness.
        for name, expected in self.snapshots.items():
            actual, _ = self._read(name)
            require(actual == expected, "input_changed_during_audit")
            self.final_fresh_hashes += 1
        require(self.final_fresh_hashes == len(self.snapshots), "audit_final_hash_inventory")
