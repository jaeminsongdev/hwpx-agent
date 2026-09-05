from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def run(command: list[str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    run([sys.executable, "-m", "compileall", "-q", "tools/p16"])
    run([sys.executable, "tools/p16/build_universal_package_contract.py", "--check"])
    run([sys.executable, "tools/p16/validate_universal_package.py"])
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/p16/tests",
            "-p",
            "test_universal_package.py",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
