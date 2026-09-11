"""Compare historical two-process blob reads with the bounded batch reader."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.dev.git_batch import (
    GitBatchReader,
    sanitized_git_environment,
    validate_relative_path,
    validate_revision,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATHS = (
    "Cargo.lock",
    "PLANS.md",
    "crates/domain-ir/src/lib.rs",
    "tools/p17/frozen_current_source_v48.py",
)


def legacy_blob(root: Path, revision: str, relative: str) -> bytes:
    specification = f"{revision}:{relative}"
    environment = sanitized_git_environment()
    size = subprocess.run(
        ["git", "cat-file", "-s", specification],
        cwd=root,
        stdin=subprocess.DEVNULL,
        check=True,
        capture_output=True,
        env=environment,
        timeout=30,
    )
    length = int(size.stdout.decode("ascii").strip())
    if not 0 < length <= 4_000_000:
        raise ValueError("blob.size")
    content = subprocess.run(
        ["git", "cat-file", "blob", specification],
        cwd=root,
        stdin=subprocess.DEVNULL,
        check=True,
        capture_output=True,
        env=environment,
        timeout=30,
    )
    if len(content.stdout) != length:
        raise ValueError("blob.bytes")
    return content.stdout


def benchmark(revision: str, paths: tuple[str, ...], repeats: int) -> dict[str, object]:
    revision = validate_revision(revision)
    paths = tuple(validate_relative_path(path) for path in paths)
    if not 1 <= repeats <= 1_000 or not 1 <= len(paths) <= 32:
        raise ValueError("benchmark.limit")

    legacy_start = time.perf_counter()
    legacy_bytes = 0
    for _ in range(repeats):
        for path in paths:
            legacy_bytes += len(legacy_blob(ROOT, revision, path))
    legacy_seconds = time.perf_counter() - legacy_start

    batch_start = time.perf_counter()
    with GitBatchReader(ROOT) as reader:
        batch_bytes = 0
        for _ in range(repeats):
            for path in paths:
                batch_bytes += len(reader.read_blob(revision, path))
        stats = reader.stats
    batch_seconds = time.perf_counter() - batch_start
    if legacy_bytes != batch_bytes:
        raise ValueError("benchmark.bytes")
    return {
        "schema": "hwpx-agent.dev-git-batch-benchmark/v1",
        "revision": revision,
        "path_count": len(paths),
        "repeats": repeats,
        "read_count": len(paths) * repeats,
        "legacy_seconds": round(legacy_seconds, 6),
        "batch_seconds": round(batch_seconds, 6),
        "speedup": round(legacy_seconds / batch_seconds, 3),
        "bytes_verified": legacy_bytes,
        "batch_process_starts": stats.process_starts,
        "batch_object_queries": stats.object_queries,
        "batch_cache_hits": stats.cache_hits,
        "batch_cache_entries": stats.cache_entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", required=True)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--path", action="append", dest="paths")
    arguments = parser.parse_args()
    paths = tuple(arguments.paths) if arguments.paths else DEFAULT_PATHS
    result = benchmark(arguments.revision, paths, arguments.repeats)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
