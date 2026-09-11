"""Bounded Git object reads through one persistent ``git cat-file`` process.

This module is intentionally separate from the immutable P17 qualification
lineage.  New qualifications may source-lock and use it, while historical
qualifiers keep their exact committed implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import BinaryIO


MAX_BLOB_BYTES = 4_000_000
MAX_HEADER_BYTES = 256
MAX_CACHE_BYTES = 64 * 1024 * 1024
MAX_CACHE_ENTRIES = 4_096
REPOSITORY_ENVIRONMENT_KEYS = (
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_NAMESPACE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_WORK_TREE",
)
HEX_REVISION = re.compile(r"[0-9a-f]{40}\Z")
HEX_OBJECT = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


class GitBatchError(ValueError):
    """Fail-closed error containing only a bounded diagnostic code."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise GitBatchError(code)


def validate_revision(revision: str) -> str:
    _require(
        isinstance(revision, str) and HEX_REVISION.fullmatch(revision) is not None,
        "revision",
    )
    return revision


def validate_relative_path(relative: str) -> str:
    _require(
        isinstance(relative, str)
        and 0 < len(relative) <= 240
        and "\\" not in relative
        and ":" not in relative
        and all(ord(character) >= 0x20 for character in relative),
        "path",
    )
    value = PurePosixPath(relative)
    _require(
        not value.is_absolute()
        and value.as_posix() == relative
        and all(part not in ("", ".", "..") for part in value.parts),
        "path",
    )
    return relative


def sanitized_git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in REPOSITORY_ENVIRONMENT_KEYS:
        environment.pop(key, None)
    environment.update(
        {
            "GCM_INTERACTIVE": "Never",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


@dataclass(frozen=True)
class GitBatchStats:
    process_starts: int
    object_queries: int
    cache_hits: int
    cache_entries: int
    cached_bytes: int


class GitBatchReader:
    """Read exact historical blobs with bounded memory and process reuse."""

    def __init__(self, root: Path, *, max_blob_bytes: int = MAX_BLOB_BYTES) -> None:
        _require(
            type(max_blob_bytes) is int and 0 < max_blob_bytes <= MAX_BLOB_BYTES,
            "blob.limit",
        )
        try:
            resolved = root.resolve(strict=True)
        except OSError as error:
            raise GitBatchError("git.root") from error
        _require(resolved.is_dir(), "git.root")
        self._root = resolved
        self._max_blob_bytes = max_blob_bytes
        self._environment = sanitized_git_environment()
        self._process: subprocess.Popen[bytes] | None = None
        self._input: BinaryIO | None = None
        self._output: BinaryIO | None = None
        self._cache: dict[tuple[str, str], bytes] = {}
        self._cached_bytes = 0
        self._object_queries = 0
        self._cache_hits = 0
        self._process_starts = 0
        self._verify_repository()

    def __repr__(self) -> str:
        state = "open" if self._process is not None else "idle"
        return (
            "GitBatchReader("
            f"state={state!r}, cache_entries={len(self._cache)}, "
            f"object_queries={self._object_queries})"
        )

    def __enter__(self) -> GitBatchReader:
        return self

    def __exit__(self, _kind: object, _value: object, _traceback: object) -> None:
        self.close()

    @property
    def stats(self) -> GitBatchStats:
        return GitBatchStats(
            process_starts=self._process_starts,
            object_queries=self._object_queries,
            cache_hits=self._cache_hits,
            cache_entries=len(self._cache),
            cached_bytes=self._cached_bytes,
        )

    def _verify_repository(self) -> None:
        try:
            completed = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=self._root,
                stdin=subprocess.DEVNULL,
                check=False,
                capture_output=True,
                env=self._environment,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise GitBatchError("git.root") from error
        _require(completed.returncode == 0 and len(completed.stdout) <= 4096, "git.root")
        try:
            observed = Path(completed.stdout.decode("utf-8").strip()).resolve(strict=True)
        except (OSError, UnicodeDecodeError) as error:
            raise GitBatchError("git.root") from error
        _require(observed == self._root, "git.root")

    def _start(self) -> None:
        if self._process is not None:
            _require(self._process.poll() is None, "git.process")
            return
        try:
            process = subprocess.Popen(
                ["git", "cat-file", "--batch"],
                cwd=self._root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env=self._environment,
                bufsize=0,
            )
        except OSError as error:
            raise GitBatchError("git.process") from error
        _require(process.stdin is not None and process.stdout is not None, "git.process")
        self._process = process
        self._input = process.stdin
        self._output = process.stdout
        self._process_starts += 1

    def read_blob(
        self,
        revision: str,
        relative: str,
        *,
        maximum: int | None = None,
    ) -> bytes:
        revision = validate_revision(revision)
        relative = validate_relative_path(relative)
        limit = self._max_blob_bytes if maximum is None else maximum
        _require(type(limit) is int and 0 < limit <= self._max_blob_bytes, "blob.limit")
        key = (revision, relative)
        cached = self._cache.get(key)
        if cached is not None:
            _require(len(cached) <= limit, "blob.size")
            self._cache_hits += 1
            return cached

        self._start()
        _require(self._input is not None and self._output is not None, "git.process")
        specification = f"{revision}:{relative}".encode("utf-8")
        try:
            self._input.write(specification + b"\n")
            self._input.flush()
            header = self._output.readline(MAX_HEADER_BYTES + 1)
        except (BrokenPipeError, OSError) as error:
            raise GitBatchError("git.process") from error
        _require(0 < len(header) <= MAX_HEADER_BYTES and header.endswith(b"\n"), "blob.header")
        try:
            fields = header[:-1].decode("ascii").split(" ")
        except UnicodeDecodeError as error:
            raise GitBatchError("blob.header") from error
        _require(len(fields) == 3, "blob.header")
        object_id, object_type, size_text = fields
        _require(HEX_OBJECT.fullmatch(object_id) is not None, "blob.object")
        _require(object_type == "blob", "blob.type")
        try:
            size = int(size_text)
        except ValueError as error:
            raise GitBatchError("blob.size") from error
        _require(size_text.isdecimal() and 0 < size <= limit, "blob.size")
        try:
            raw = self._read_exact(size)
            terminator = self._read_exact(1)
        except OSError as error:
            raise GitBatchError("blob.read") from error
        _require(len(raw) == size and terminator == b"\n", "blob.bytes")
        if (
            len(self._cache) < MAX_CACHE_ENTRIES
            and self._cached_bytes + len(raw) <= MAX_CACHE_BYTES
        ):
            self._cache[key] = raw
            self._cached_bytes += len(raw)
        self._object_queries += 1
        return raw

    def _read_exact(self, length: int) -> bytes:
        _require(self._output is not None, "git.process")
        chunks = bytearray()
        while len(chunks) < length:
            chunk = self._output.read(length - len(chunks))
            _require(bool(chunk), "blob.bytes")
            chunks.extend(chunk)
        return bytes(chunks)

    def close(self) -> None:
        process = self._process
        self._process = None
        input_stream = self._input
        self._input = None
        output_stream = self._output
        self._output = None
        if process is None:
            return
        if input_stream is not None:
            try:
                input_stream.close()
            except OSError:
                pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        if output_stream is not None:
            output_stream.close()
