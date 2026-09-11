"""Fixed validation profiles executed through the live development runner."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.dev.run import execute


@dataclass(frozen=True)
class Profile:
    authority: str
    commands: tuple[tuple[str, ...], ...]


PROFILES = {
    "dev-tools": Profile(
        "component",
        (
            (
                "python",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tools/dev/tests",
                "-p",
                "test_*.py",
                "-v",
            ),
        ),
    ),
    "p07-focused": Profile(
        "component",
        (
            (
                "cargo",
                "test",
                "-p",
                "domain-ir",
                "--test",
                "math_ast",
                "--locked",
                "--offline",
            ),
            (
                "cargo",
                "test",
                "-p",
                "equation-engine",
                "--all-targets",
                "--locked",
                "--offline",
            ),
            (
                "python",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tools/p07/tests",
                "-p",
                "test_*.py",
                "-v",
            ),
        ),
    ),
    "p17-fast": Profile(
        "development_feedback_only",
        (("python", "tools/dev/p17_fast.py"),),
    ),
    "p17-full": Profile(
        "closure_validation",
        (
            (
                "python",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tools/p17/tests",
                "-p",
                "test_*.py",
                "-v",
            ),
        ),
    ),
    "rust-full": Profile(
        "closure_validation",
        (
            (
                "cargo",
                "test",
                "--workspace",
                "--all-targets",
                "--all-features",
                "--locked",
                "--offline",
            ),
            (
                "cargo",
                "clippy",
                "--workspace",
                "--all-targets",
                "--all-features",
                "--locked",
                "--offline",
                "--",
                "-D",
                "warnings",
            ),
            ("cargo", "fmt", "--all", "--", "--check"),
        ),
    ),
}


def catalog() -> dict[str, object]:
    return {
        "schema": "hwpx-agent.development-validation-profiles/v1",
        "profiles": {
            name: {
                "authority": profile.authority,
                "stage_count": len(profile.commands),
            }
            for name, profile in sorted(PROFILES.items())
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=sorted(PROFILES))
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--heartbeat-seconds", type=float, default=10.0)
    parser.add_argument("--sccache", action="store_true")
    arguments = parser.parse_args()
    if arguments.list:
        print(json.dumps(catalog(), ensure_ascii=True, sort_keys=True, separators=(",", ":")))
        return 0
    if arguments.profile is None:
        parser.error("--profile is required unless --list is used")
    profile = PROFILES[arguments.profile]
    print(
        json.dumps(
            {
                "schema": "hwpx-agent.development-validation-start/v1",
                "profile": arguments.profile,
                "authority": profile.authority,
                "stage_count": len(profile.commands),
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    for index, command in enumerate(profile.commands, start=1):
        result = execute(
            list(command),
            name=f"{arguments.profile}-{index:02d}",
            heartbeat_seconds=arguments.heartbeat_seconds,
            use_sccache=arguments.sccache,
        )
        if result.exit_code != 0:
            return result.exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
