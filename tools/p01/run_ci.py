#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LANES = ("linux-core", "windows-worker", "widget", "docs", "security")


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    if os.name == "nt" and command[0] == "pnpm":
        command[0] = shutil.which("pnpm.cmd") or "pnpm.cmd"
    print(f"+ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def linux_core() -> None:
    run(["cargo", "fmt", "--all", "--", "--check"])
    run(["cargo", "clippy", "--locked", "--workspace", "--all-targets", "--", "-D", "warnings"])
    run(["cargo", "test", "--locked", "--workspace"])
    run(["cargo", "run", "--locked", "-p", "xtask", "--", "generate", "--check"])


def windows_worker() -> None:
    if os.name != "nt":
        raise RuntimeError("windows-worker lane requires Windows")
    projects = (
        "workers/windows-hancom-worker/tests/HwpxAgent.WindowsWorker.Smoke/HwpxAgent.WindowsWorker.Smoke.csproj",
        "workers/windows-hancom-worker/tests/HwpxAgent.WindowsWorker.StaSmoke/HwpxAgent.WindowsWorker.StaSmoke.csproj",
        "workers/windows-hancom-worker/tests/HwpxAgent.WindowsWorker.LifecycleSmoke/HwpxAgent.WindowsWorker.LifecycleSmoke.csproj",
        "workers/windows-hancom-worker/tests/HwpxAgent.WindowsWorker.SecuritySmoke/HwpxAgent.WindowsWorker.SecuritySmoke.csproj",
        "workers/windows-hancom-worker/tests/HwpxAgent.WindowsWorker.BindingSmoke/HwpxAgent.WindowsWorker.BindingSmoke.csproj",
        "workers/windows-hancom-worker/tests/HwpxAgent.WindowsWorker.ModalWatchdogSmoke/HwpxAgent.WindowsWorker.ModalWatchdogSmoke.csproj",
        "workers/windows-hancom-agent/tests/HwpxAgent.WindowsAgent.Smoke/HwpxAgent.WindowsAgent.Smoke.csproj",
    )
    for project in projects:
        run(["dotnet", "restore", "--locked-mode", project])
        run(["dotnet", "format", project, "--verify-no-changes", "--no-restore"])
        run(["dotnet", "build", "--no-restore", "--configuration", "Release", project])
        run(["dotnet", "run", "--no-build", "--configuration", "Release", "--project", project])
    run(["pwsh", "-NoProfile", "-File", "implementation/p10/tests/Test-Hancom2020Lifecycle.ps1"])
    run(["pwsh", "-NoProfile", "-File", "implementation/p10/tests/Test-Hancom2020SecurityAdapter.ps1"])
    run(["pwsh", "-NoProfile", "-File", "implementation/p10/tests/Test-Hancom2020BindingExecutor.ps1"])
    run(["pwsh", "-NoProfile", "-File", "implementation/p10/tests/Test-Hancom2020EventModalWatchdog.ps1"])
    run(["pwsh", "-NoProfile", "-File", "implementation/p10/tests/Test-Hancom2020Isolation.ps1"])
    run(["pwsh", "-NoProfile", "-File", "implementation/p10/tests/Test-Hancom2020Supervisor.ps1"])
    run(["pwsh", "-NoProfile", "-File", "implementation/p10/tests/Test-Hancom2020RuntimeProbe.ps1"])
    run([sys.executable, "implementation/p10/tests/validate_binding_schemas.py"])
    run(
        [
            sys.executable,
            "tools/p10/validate_worker_isolation.py",
            "--policy",
            "implementation/p10/isolation/p10-current-pc-local-worker-policy.json",
        ]
    )
    run(
        [
            sys.executable,
            "tools/p10/validate_worker_supervision.py",
            "--policy",
            "implementation/p10/supervision/p10-current-pc-worker-supervisor-policy.json",
        ]
    )
    run(
        [
            sys.executable,
            "tools/p10/validate_runtime_probe.py",
            "--policy",
            "implementation/p10/probe/p10-current-pc-runtime-probe-policy.json",
        ]
    )


def widget() -> None:
    run(["pnpm", "install", "--frozen-lockfile"])
    run(["pnpm", "run", "format:check"])
    run(["pnpm", "-r", "typecheck"])
    run(["pnpm", "-r", "build"])
    run(["pnpm", "-r", "test"])


def docs() -> None:
    run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "tools/p01",
            "tools/p02",
            "tools/p04",
            "tools/p10",
            "tools/p14",
            "tools/p15",
            "tools/p06",
        ]
    )
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/p01/tests",
            "-p",
            "test_*.py",
        ]
    )
    run([sys.executable, "tools/design-validation/validate_design.py"])
    run([sys.executable, "tools/p01/validate_foundation.py"])
    run([sys.executable, "tools/p02/validate_source_records.py"])
    run([sys.executable, "tools/p04/verify_route_attestation.py"])
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/p04/tests",
            "-p",
            "test_*.py",
        ]
    )
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/p02/tests",
            "-p",
            "test_*.py",
        ]
    )
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/p10/tests",
            "-p",
            "test_*.py",
        ]
    )
    run([sys.executable, "tools/p14/validate_metadata_migrations.py"])
    run([sys.executable, "tools/p14/validate_artifact_service_migration.py"])
    run([sys.executable, "tools/p14/validate_revision_cas_migration.py"])
    run([sys.executable, "tools/p14/validate_history_checkpoints_migration.py"])
    run([sys.executable, "tools/p14/validate_job_state_machine_migration.py"])
    run([sys.executable, "tools/p14/validate_worker_lease_fencing_migration.py"])
    run([sys.executable, "tools/p14/validate_idempotency_reconciliation_core.py"])
    run([sys.executable, "tools/p14/validate_idempotency_reconciliation_migration.py"])
    run([sys.executable, "tools/p14/validate_cancel_cleanup.py"])
    run([sys.executable, "tools/p14/validate_retention_local_mirror.py"])
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/p14/tests",
            "-p",
            "test_*.py",
        ]
    )
    run([sys.executable, "tools/p15/validate_auth_tenant.py"])
    run([sys.executable, "tools/p15/build_public_tool_schemas.py", "--check"])
    run([sys.executable, "tools/p15/validate_public_tool_schemas.py"])
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/p15/tests",
            "-p",
            "test_*.py",
        ]
    )
    run([sys.executable, "tools/p06/validate_table_grid_contract.py"])
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/p06/tests",
            "-p",
            "test_*.py",
        ]
    )
    run([sys.executable, "tools/p01/check_docs.py"])


def security() -> None:
    run([sys.executable, "tools/p01/security_checks.py"])


FUNCTIONS = {
    "linux-core": linux_core,
    "windows-worker": windows_worker,
    "widget": widget,
    "docs": docs,
    "security": security,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", choices=(*LANES, "all"), default="all")
    arguments = parser.parse_args()
    selected = LANES if arguments.lane == "all" else (arguments.lane,)
    results: list[dict[str, object]] = []
    for lane in selected:
        started = time.monotonic()
        try:
            FUNCTIONS[lane]()
        except (subprocess.CalledProcessError, RuntimeError) as error:
            results.append({"lane": lane, "status": "failed", "seconds": round(time.monotonic() - started, 3), "error": str(error)})
            print(json.dumps({"lanes": results}, ensure_ascii=False, indent=2))
            return 1
        results.append({"lane": lane, "status": "passed", "seconds": round(time.monotonic() - started, 3)})
    print(json.dumps({"lanes": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
