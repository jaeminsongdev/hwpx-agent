#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "implementation" / "p01" / "evidence"
POLICY = json.loads((ROOT / "security" / "dependency-policy.json").read_text(encoding="utf-8"))


def capture(command: list[str], *, allow_stderr: bool = True) -> dict[str, object]:
    if os.name == "nt" and command[0] == "pnpm":
        command[0] = shutil.which("pnpm.cmd") or "pnpm.cmd"
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if result.stdout:
        print(result.stdout.rstrip())
    if allow_stderr and result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    return {"command": command, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


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


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    checks: dict[str, dict[str, object]] = {}
    checks["secret_scan"] = capture([sys.executable, "tools/p01/scan_secrets.py"])
    checks["cargo_deny"] = capture(["cargo", "deny", "check"])
    checks["cargo_audit"] = capture(["cargo", "audit", "--json"])
    checks["pnpm_audit"] = capture(["pnpm", "audit", "--audit-level", "high", "--json"])
    checks["pnpm_licenses"] = capture(["pnpm", "licenses", "list", "--json"])
    dotnet_projects = {
        "dotnet_vulnerable_windows_worker": "workers/windows-hancom-worker/tests/HwpxAgent.WindowsWorker.LifecycleSmoke/HwpxAgent.WindowsWorker.LifecycleSmoke.csproj",
        "dotnet_vulnerable_windows_agent": "workers/windows-hancom-agent/tests/HwpxAgent.WindowsAgent.Smoke/HwpxAgent.WindowsAgent.Smoke.csproj",
    }
    for check_name, project in dotnet_projects.items():
        checks[check_name] = capture(
            ["dotnet", "list", project, "package", "--vulnerable", "--include-transitive", "--format", "json"]
        )

    sbom_path = EVIDENCE / "sbom.cdx.json"
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
            allowed = set(POLICY["allowed_licenses"])
            license_errors.extend(
                f"Node license not allowlisted: {license_name}"
                for license_name in node_licenses
                if license_name not in allowed
            )
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
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "current_pc_local_repository_only",
        "checks": {name: {"exit_code": result["exit_code"]} for name, result in checks.items()},
        "license_errors": license_errors,
        "forbidden_license_count": len(license_errors),
        "sbom_components": sbom_components,
        "failed_checks": failed,
    }
    report_path = EVIDENCE / "security-report.20260901.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failed or license_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
