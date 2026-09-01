#!/usr/bin/env python3
from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
LOCK = json.loads((ROOT / "toolchains.lock.json").read_text(encoding="utf-8"))


def output(*command: str) -> str:
    executable = command[0]
    if sys.platform == "win32" and executable == "pnpm":
        executable = shutil.which("pnpm.cmd") or "pnpm.cmd"
    result = subprocess.run((executable, *command[1:]), cwd=ROOT, check=True, text=True, capture_output=True)
    return result.stdout.strip()


def exact_version(label: str, actual: str, expected: str, errors: list[str]) -> None:
    if actual != expected:
        errors.append(f"{label}: expected {expected}, actual {actual}")


def main() -> int:
    errors: list[str] = []
    observations: dict[str, str] = {}
    commands = {
        "rustc": ("rustc", "--version"),
        "cargo": ("cargo", "--version"),
        "dotnet": ("dotnet", "--version"),
        "node": ("node", "--version"),
        "pnpm": ("pnpm", "--version"),
        "cargo_deny": ("cargo", "deny", "--version"),
        "cargo_audit": ("cargo", "audit", "--version"),
        "syft": ("syft", "version"),
    }
    for label, command in commands.items():
        try:
            value = output(*command)
            if label in {"rustc", "cargo"}:
                observations[label] = value.split()[1]
            elif label in {"cargo_deny", "cargo_audit"}:
                match = re.search(r"\d+\.\d+\.\d+", value)
                observations[label] = match.group(0) if match else value
            elif label == "syft":
                match = re.search(r"(?m)^Version:\s*(\S+)", value)
                observations[label] = match.group(1) if match else value
            else:
                observations[label] = value.removeprefix("v")
        except (subprocess.CalledProcessError, FileNotFoundError) as error:
            errors.append(f"{label} discovery failed: {error}")
    observations["python"] = ".".join(str(part) for part in sys.version_info[:3])
    for package in ("PyYAML", "jsonschema", "pdfminer.six"):
        try:
            observations[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError as error:
            errors.append(f"{package} discovery failed: {error}")

    exact_version("rustc", observations.get("rustc", "missing"), LOCK["rust"]["toolchain"], errors)
    exact_version("cargo", observations.get("cargo", "missing"), LOCK["rust"]["cargo"], errors)
    exact_version("dotnet", observations.get("dotnet", "missing"), LOCK["dotnet"]["sdk"], errors)
    exact_version("node", observations.get("node", "missing"), LOCK["node"]["runtime"], errors)
    exact_version("pnpm", observations.get("pnpm", "missing"), LOCK["node"]["pnpm"], errors)
    exact_version("PyYAML", observations.get("PyYAML", "missing"), LOCK["python"]["pyyaml"], errors)
    exact_version("jsonschema", observations.get("jsonschema", "missing"), LOCK["python"]["jsonschema"], errors)
    exact_version(
        "pdfminer.six",
        observations.get("pdfminer.six", "missing"),
        LOCK["python"]["pdfminer_six"],
        errors,
    )
    exact_version("cargo-deny", observations.get("cargo_deny", "missing"), LOCK["security"]["cargo_deny"], errors)
    exact_version("cargo-audit", observations.get("cargo_audit", "missing"), LOCK["security"]["cargo_audit"], errors)
    exact_version("syft", observations.get("syft", "missing"), LOCK["security"]["syft"], errors)
    if not re.fullmatch(r"3\.13\.\d+", observations.get("python", "")):
        errors.append(f"python: expected 3.13.x, actual {observations.get('python', 'missing')}")

    print(json.dumps({"observations": observations, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
