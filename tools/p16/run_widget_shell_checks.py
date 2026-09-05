from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "web/plugin-widget/dist/widget-v1.html"


def run(command: list[str]) -> None:
    if os.name == "nt" and command[0] == "pnpm":
        command[0] = shutil.which("pnpm.cmd") or "pnpm.cmd"
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def bundle_sha256() -> str:
    return hashlib.sha256(BUNDLE.read_bytes()).hexdigest()


def main() -> int:
    run([sys.executable, "-m", "compileall", "-q", "tools/p16"])
    run(["pnpm", "--filter", "@hwpx-agent/plugin-widget", "typecheck"])
    run(["pnpm", "--filter", "@hwpx-agent/plugin-widget", "build"])
    first = bundle_sha256()
    run(["pnpm", "--filter", "@hwpx-agent/plugin-widget", "build:widget"])
    if first != bundle_sha256():
        raise RuntimeError("widget bundle is not deterministic")
    run(["pnpm", "--filter", "@hwpx-agent/plugin-widget", "test"])
    run([sys.executable, "tools/p16/build_widget_shell_contract.py", "--check"])
    run([sys.executable, "tools/p16/validate_widget_shell.py"])
    run([
        sys.executable, "-m", "unittest", "discover", "-s", "tools/p16/tests",
        "-p", "test_widget_shell.py",
    ])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
