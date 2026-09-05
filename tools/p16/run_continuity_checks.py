from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "web/plugin-widget/dist/continuity-widget-v1.html"


def run(command: list[str]) -> None:
    if os.name == "nt" and command[0] == "pnpm":
        command[0] = shutil.which("pnpm.cmd") or "pnpm.cmd"
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def digest() -> str:
    return hashlib.sha256(BUNDLE.read_bytes()).hexdigest()


def main() -> int:
    run([sys.executable, "-m", "compileall", "-q", "tools/p16"])
    run(["pnpm", "--filter", "@hwpx-agent/plugin-widget", "typecheck"])
    run(["pnpm", "--filter", "@hwpx-agent/plugin-widget", "build"])
    run(["node", "web/plugin-widget/scripts/build-continuity-widget.mjs"])
    first = digest()
    run(["node", "web/plugin-widget/scripts/build-continuity-widget.mjs"])
    if first != digest():
        raise RuntimeError("continuity bundle is not deterministic")
    run(["pnpm", "--filter", "@hwpx-agent/plugin-widget", "test"])
    run([sys.executable, "tools/p16/build_continuity_contract.py", "--check"])
    run([sys.executable, "tools/p16/validate_continuity.py"])
    run([
        sys.executable, "-m", "unittest", "discover", "-s", "tools/p16/tests",
        "-p", "test_continuity.py",
    ])
    run([sys.executable, "tools/p16/run_continuity_e2e.py", "--publish"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
