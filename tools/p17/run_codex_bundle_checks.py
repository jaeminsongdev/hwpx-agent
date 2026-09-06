from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import tempfile

import codex_bundle


ROOT = Path(__file__).resolve().parents[2]


def command(arguments: list[str]) -> None:
    print("+ " + " ".join(arguments))
    subprocess.run(arguments, cwd=ROOT, check=True)


def main() -> int:
    command([sys.executable, "-m", "compileall", "-q", "tools/p17"])
    command(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/p17/tests",
            "-p",
            "test_codex_bundle.py",
        ]
    )
    with tempfile.TemporaryDirectory(prefix="hwpx-agent-p17-bundle-") as directory:
        archive = Path(directory) / "hwpx-agent-codex-core-0.1.0.zip"
        command([sys.executable, "tools/p17/build_codex_bundle.py", "--output", str(archive)])
        errors = codex_bundle.validate_archive(archive)
        if errors:
            raise RuntimeError(",".join(errors))
    print('{"decision":"PASS","entries":19,"registered_remote_app":false}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
