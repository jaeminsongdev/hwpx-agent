"""Verify the immutable post-v39 P14 cancel-validator successor."""

from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import frozen_current_source_v39 as frozen  # noqa: E402
from tools.p17 import frozen_source_successor_pairs_v1 as pairs  # noqa: E402

ANCHOR_COMMIT = frozen.QUALIFICATION_COMMIT
SUCCESSOR_COMMIT = "ca58d79b9270dedac68ad8c67d21c5182b3f72c7"
RELATIVE = "tools/p14/validate_cancel_cleanup.py"
P15_PREDECESSOR_SHA256 = (
    "b1b6f3ae67d28ac42e5cdd18d7dcc787f8f7fcfd59dcdf9f441d095d5eaf10da"
)
ANCHOR_BYTES = 14_835
ANCHOR_SHA256 = "0e55cd4b00a1d670b1c31238fc69e9933db68e52c95a41ec18bb709c0be128c0"
SUCCESSOR_BYTES = 15_800
SUCCESSOR_SHA256 = "e8327d846f319148edf7e94f222cfd731a37f3e83176c7789b846b6c2b41aecb"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenP14CancelSuccessorError(ValueError):
    """Fail-closed exact P14 cancel-validator successor error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenP14CancelSuccessorError(code)


def verified_replacement(
    root: Path = ROOT,
    source_lock: dict[str, Any] | None = None,
) -> tuple[str, str]:
    require(
        isinstance(source_lock, dict)
        and set(source_lock) == {"path", "sha256"}
        and source_lock.get("path") == RELATIVE
        and source_lock.get("sha256") == P15_PREDECESSOR_SHA256,
        "source_lock.identity",
    )
    if not isinstance(source_lock, dict):
        raise FrozenP14CancelSuccessorError("source_lock.identity")
    predecessor = source_lock.get("sha256")
    require(
        isinstance(predecessor, str) and HEX64.fullmatch(predecessor) is not None,
        "source_lock.digest",
    )
    frozen.verify_commit(root, ANCHOR_COMMIT)
    frozen.verify_commit(root, SUCCESSOR_COMMIT)
    frozen.require_ancestor(root, ANCHOR_COMMIT, SUCCESSOR_COMMIT)
    pair = pairs.p15_context_replacements(root, [source_lock], "p15_auth").get(RELATIVE)
    require(
        pair == (P15_PREDECESSOR_SHA256, ANCHOR_SHA256),
        "anchor.pair",
    )
    anchor_raw = frozen.git_blob(root, ANCHOR_COMMIT, RELATIVE, 64_000)
    require(len(anchor_raw) == ANCHOR_BYTES, "anchor.bytes")
    require(frozen.digest(anchor_raw) == ANCHOR_SHA256, "anchor.digest")
    successor_raw = frozen.git_blob(root, SUCCESSOR_COMMIT, RELATIVE, 64_000)
    require(len(successor_raw) == SUCCESSOR_BYTES, "successor.bytes")
    require(frozen.digest(successor_raw) == SUCCESSOR_SHA256, "successor.digest")
    return P15_PREDECESSOR_SHA256, SUCCESSOR_SHA256


if __name__ == "__main__":
    raise SystemExit("library-only immutable verifier")
