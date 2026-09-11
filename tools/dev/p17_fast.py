"""Run P17 development tests without replaying expensive closure evidence.

This is feedback-only.  A P17 closure still requires the complete discovery
suite, including every excluded historical and tamper test.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TEST_ROOT = ROOT / "tools" / "p17" / "tests"
DEFERRED_CLOSURE = re.compile(
    r"test_(?:.*qualification.*|frozen_.*|telemetry_source_successor_bridge)\.py\Z"
)


def classify() -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    candidates = tuple(sorted(TEST_ROOT.glob("test_*.py")))
    fast = tuple(path for path in candidates if DEFERRED_CLOSURE.fullmatch(path.name) is None)
    deferred = tuple(path for path in candidates if DEFERRED_CLOSURE.fullmatch(path.name) is not None)
    if len(candidates) != len(fast) + len(deferred) or not deferred:
        raise ValueError("p17.plan")
    return fast, deferred


def module_name(path: Path) -> str:
    relative = path.relative_to(ROOT).with_suffix("")
    return ".".join(relative.parts)


def plan() -> dict[str, object]:
    fast, deferred = classify()
    return {
        "schema": "hwpx-agent.p17-development-validation-plan/v1",
        "authority": "development_feedback_only",
        "fast_file_count": len(fast),
        "deferred_closure_file_count": len(deferred),
        "deferred_patterns": [
            "qualification_replay",
            "frozen_authority_replay",
            "source_successor_bridge",
        ],
        "full_closure_command": (
            'python -m unittest discover -s tools/p17/tests -p "test_*.py"'
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    arguments = parser.parse_args()
    fast, _deferred = classify()
    print(json.dumps(plan(), ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    if arguments.list:
        return 0
    suite = unittest.defaultTestLoader.loadTestsFromNames(
        [module_name(path) for path in fast]
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
