from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def run(command: list[str]) -> None:
    print(f"+ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the offline P16 contract checks.")
    parser.parse_args()
    run([sys.executable, "-m", "compileall", "-q", "tools/p16"])
    run([sys.executable, "tools/p16/build_official_source_contract.py", "--check"])
    run([sys.executable, "tools/p16/validate_official_source_contract.py"])
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/p16/tests",
            "-p",
            "test_*.py",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
