#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "implementation" / "p01" / "evidence"
POLICY = json.loads((ROOT / "security" / "dependency-policy.json").read_text(encoding="utf-8"))
PNPM_AUDIT_ATTEMPTS = 3
PNPM_AUDIT_TIMEOUT_SECONDS = 60
PNPM_AUDIT_TRANSIENT_MARKERS = (
    "operation was aborted due to timeout",
    "etimedout",
    "econnreset",
    "eai_again",
    "enotfound",
    "socket hang up",
    "network timeout",
)


def print_console(value: str, *, stream: object | None = None) -> None:
    destination = sys.stdout if stream is None else stream
    encoding = getattr(destination, "encoding", None) or "utf-8"
    safe_value = value.encode(encoding, errors="backslashreplace").decode(encoding)
    print(safe_value, file=destination)


def resolved_command(command: list[str]) -> list[str]:
    resolved = list(command)
    if os.name == "nt" and resolved[0] == "pnpm":
        resolved[0] = shutil.which("pnpm.cmd") or "pnpm.cmd"
    return resolved


def terminate_process_tree(process: subprocess.Popen[str]) -> bool:
    if process.poll() is not None:
        return True
    tree_kill_succeeded = True
    try:
        if os.name == "nt":
            taskkill = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            tree_kill_succeeded = taskkill.returncode == 0
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)
    except (OSError, subprocess.SubprocessError):
        try:
            process.kill()
            process.wait(timeout=5)
        except (OSError, subprocess.SubprocessError):
            return False
        return False
    return tree_kill_succeeded and process.poll() is not None


def capture(
    command: list[str],
    *,
    allow_stderr: bool = True,
    timeout_seconds: float | None = None,
) -> dict[str, object]:
    resolved = resolved_command(command)
    popen_arguments: dict[str, object] = {}
    if os.name != "nt":
        popen_arguments["start_new_session"] = True
    process = subprocess.Popen(
        resolved,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        **popen_arguments,
    )
    timed_out = False
    cleanup_succeeded = True
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        exit_code = process.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        cleanup_succeeded = terminate_process_tree(process)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            stdout, stderr = "", ""
            cleanup_succeeded = False
        timeout_message = f"command exceeded {timeout_seconds:g} second timeout"
        stderr = f"{stderr.rstrip()}\n{timeout_message}".lstrip()
        exit_code = 124 if cleanup_succeeded else 125
    if stdout:
        print_console(stdout.rstrip())
    if allow_stderr and stderr:
        print_console(stderr.rstrip(), stream=sys.stderr)
    return {
        "command": resolved,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": timed_out,
        "cleanup_succeeded": cleanup_succeeded,
    }


def is_transient_pnpm_audit_failure(result: dict[str, object]) -> bool:
    if result.get("cleanup_succeeded") is False:
        return False
    if result.get("timed_out") is True:
        return True
    try:
        audit_report = json.loads(str(result.get("stdout", "")))
    except json.JSONDecodeError:
        audit_report = None
    if isinstance(audit_report, dict) and any(
        key in audit_report for key in ("auditReportVersion", "advisories", "vulnerabilities", "metadata")
    ):
        return False
    output = f"{result.get('stdout', '')}\n{result.get('stderr', '')}".lower()
    return any(marker in output for marker in PNPM_AUDIT_TRANSIENT_MARKERS)


def capture_pnpm_audit() -> dict[str, object]:
    history: list[dict[str, object]] = []
    result: dict[str, object] = {}
    command = ["pnpm", "audit", "--audit-level", "high", "--json"]
    for attempt in range(1, PNPM_AUDIT_ATTEMPTS + 1):
        result = capture(command, timeout_seconds=PNPM_AUDIT_TIMEOUT_SECONDS)
        transient = result["exit_code"] != 0 and is_transient_pnpm_audit_failure(result)
        history.append(
            {
                "attempt": attempt,
                "exit_code": result["exit_code"],
                "timed_out": result["timed_out"],
                "cleanup_succeeded": result["cleanup_succeeded"],
                "transient_failure": transient,
            }
        )
        if result["exit_code"] == 0 or not transient or attempt == PNPM_AUDIT_ATTEMPTS:
            break
        message = f"pnpm audit transient failure; retrying attempt {attempt + 1}/{PNPM_AUDIT_ATTEMPTS}"
        print_console(message, stream=sys.stderr)
        time.sleep(1)
    result["attempt_history"] = history
    result["attempt_count"] = len(history)
    return result


def create_evidence_run() -> tuple[str, Path]:
    run_id = uuid.uuid4().hex
    run_root = EVIDENCE / "security-runs" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    return run_id, run_root


def nuget_license_errors() -> list[str]:
    errors: list[str] = []
    locks = sorted(ROOT.glob("**/packages.lock.json"))
    allowed = set(POLICY["allowed_licenses"])
    for lock_path in locks:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        packages: dict[str, str] = {}
        for framework in lock["dependencies"].values():
            for package, metadata in framework.items():
                if metadata.get("type") in {"Direct", "Transitive"}:
                    packages[package] = metadata["resolved"]
        for package, version in packages.items():
            nuspec = Path.home() / ".nuget" / "packages" / package.lower() / version.lower() / f"{package.lower()}.nuspec"
            if not nuspec.is_file():
                errors.append(f"NuGet license evidence missing: {package} {version}")
                continue
            root = ET.parse(nuspec).getroot()
            license_node = next((node for node in root.iter() if node.tag.endswith("license")), None)
            expression = license_node.text.strip() if license_node is not None and license_node.text else ""
            if expression not in allowed:
                errors.append(f"NuGet license not allowlisted: {package} {version} {expression or 'unknown'}")
    return errors


def node_license_errors(
    report: object, policy: dict[str, object] = POLICY
) -> list[str]:
    if not isinstance(report, dict):
        return ["Node license report root is invalid"]
    allowed = set(policy.get("allowed_licenses", []))
    raw_exceptions = policy.get("node_license_exceptions", [])
    exceptions = raw_exceptions if isinstance(raw_exceptions, list) else []
    errors: list[str] = []
    for license_name, packages in report.items():
        if license_name in allowed:
            continue
        if not isinstance(license_name, str) or not isinstance(packages, list):
            errors.append("Node license report entry is invalid")
            continue
        for package in packages:
            if not isinstance(package, dict):
                errors.append(f"Node license not allowlisted: {license_name} unknown")
                continue
            name = package.get("name")
            versions = package.get("versions")
            accepted = any(
                isinstance(exception, dict)
                and exception.get("license") == license_name
                and isinstance(exception.get("packages"), list)
                and name in exception["packages"]
                and isinstance(versions, list)
                and versions == [exception.get("version")]
                for exception in exceptions
            )
            if not accepted:
                safe_name = name if isinstance(name, str) else "unknown"
                errors.append(f"Node license not allowlisted: {license_name} {safe_name}")
    return errors


def main() -> int:
    run_id, run_root = create_evidence_run()
    checks: dict[str, dict[str, object]] = {}
    checks["secret_scan"] = capture([sys.executable, "tools/p01/scan_secrets.py"])
    checks["cargo_deny"] = capture(["cargo", "deny", "check"])
    checks["cargo_audit"] = capture(["cargo", "audit", "--json"])
    checks["pnpm_audit"] = capture_pnpm_audit()
    checks["pnpm_licenses"] = capture(["pnpm", "licenses", "list", "--json"])
    dotnet_projects = {
        "dotnet_vulnerable_windows_worker": "workers/windows-hancom-worker/tests/HwpxAgent.WindowsWorker.SecuritySmoke/HwpxAgent.WindowsWorker.SecuritySmoke.csproj",
        "dotnet_vulnerable_windows_agent": "workers/windows-hancom-agent/tests/HwpxAgent.WindowsAgent.Smoke/HwpxAgent.WindowsAgent.Smoke.csproj",
    }
    for check_name, project in dotnet_projects.items():
        checks[check_name] = capture(
            ["dotnet", "list", project, "package", "--vulnerable", "--include-transitive", "--format", "json"]
        )

    sbom_path = run_root / "sbom.cdx.json"
    syft_command = [
        "syft", "scan", "dir:.",
        "--source-name", "hwpx-agent",
        "--source-version", "0.1.0",
        "--exclude", "./implementation/p00/evidence/**",
        "--exclude", "./implementation/p00/source-archive/**",
        "--exclude", "./target/**",
        "--exclude", "./node_modules/**",
        "--output", f"cyclonedx-json={sbom_path}",
    ]
    checks["sbom"] = capture(syft_command)
    license_errors = nuget_license_errors()
    if checks["pnpm_licenses"]["exit_code"] == 0:
        try:
            node_licenses = json.loads(str(checks["pnpm_licenses"]["stdout"]))
            license_errors.extend(node_license_errors(node_licenses))
        except json.JSONDecodeError as error:
            license_errors.append(f"Node license report is invalid JSON: {error}")
    try:
        sbom = json.loads(sbom_path.read_text(encoding="utf-8"))
        sbom_components = len(sbom.get("components", []))
        if sbom.get("bomFormat") != "CycloneDX" or sbom_components == 0:
            checks["sbom_content"] = {"exit_code": 1}
        else:
            checks["sbom_content"] = {"exit_code": 0}
    except (OSError, json.JSONDecodeError):
        sbom_components = 0
        checks["sbom_content"] = {"exit_code": 1}

    failed = [name for name, result in checks.items() if result["exit_code"] != 0]
    report = {
        "schema_version": "hwpx-agent.p01-security-report/v1",
        "evidence_run_id": run_id,
        "evidence_report_relative_path": (run_root / "report.json").relative_to(ROOT).as_posix(),
        "sbom_relative_path": sbom_path.relative_to(ROOT).as_posix(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "current_pc_local_repository_only",
        "checks": {
            name: {
                "exit_code": result["exit_code"],
                **(
                    {
                        "attempt_count": result["attempt_count"],
                        "attempt_history": result["attempt_history"],
                    }
                    if name == "pnpm_audit"
                    else {}
                ),
            }
            for name, result in checks.items()
        },
        "license_errors": license_errors,
        "forbidden_license_count": len(license_errors),
        "sbom_components": sbom_components,
        "failed_checks": failed,
    }
    report_path = run_root / "report.json"
    with report_path.open("x", encoding="utf-8", newline="\n") as report_file:
        report_file.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print_console(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failed or license_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
