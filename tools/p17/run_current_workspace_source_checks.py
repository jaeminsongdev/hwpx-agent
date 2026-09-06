"""Audit exact current successors for immutable P15/P16 source qualifications."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tomllib
import uuid
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "artifacts/p17/current-workspace-source-runs"
MAIN_CONTRACT = "implementation/p16/qualification/main-9cc1-p16-62542-v1/contract.json"
POSTGRES_CONTRACT = "implementation/p16/qualification/postgres-217ba56/contract.json"
P15_CONTRACT = "implementation/p16/qualification/p15-current-source-v1/contract.json"
P15_AUTH_CONTRACT = "implementation/p15/p15-auth-tenant-v1.json"
WIDGET_CONTRACT = "implementation/p16/p16-widget-shell-contract-v1.json"
RETENTION_CONTRACT = "implementation/p14/postgres/p14-retention-local-mirror-v1.json"
PINNED_CONTRACTS = {
    MAIN_CONTRACT: "890c72ac61c2c7d4e871958ff684de513fe1fe7e888e1264cba0eaec4bab52df",
    POSTGRES_CONTRACT: "c37e5b773a9117ffdb4af40c95d1263e08fdf7f6e25c69c6daa3108086497530",
    P15_CONTRACT: "5391428d584f7be36ed532ea446a07372761fb28bad9446972cef307c35a13e0",
    P15_AUTH_CONTRACT: "7bae38b349e394b53636462fe19cb8e1c057a35ab68e7c23161086af6400ad99",
    WIDGET_CONTRACT: "2d8dad6318bc9090b0a7db70d19f1470e6ce0fa97bb177755cff993f9b94f09e",
    RETENTION_CONTRACT: "080dda5dd65a7e803c49d73648691dd49971c0a8ade1b70b8521a7a5a9e6d7c5",
}
PINNED_AMBIGUOUS_BASELINES = {
    "Cargo.toml": (
        "f8281c9c13ea981ab8652819f1e3946ea942bca2d952f68b05ee61f3a3179c03"
    ),
    "tools/p15/validate_inspector_staging_contract.py": (
        "d9869d7a01b2cea5eeeb0a9d5f64dae79cccf523dbdec8811f812551ef16d7d3"
    ),
}
HEX = re.compile(r"[0-9a-f]{64}\Z")
CHECKS = (
    "clean_tracked_source",
    "immutable_predecessor_contracts_exact",
    "source_paths_bounded_regular_files",
    "predecessor_hash_sets_derived_from_exact_contracts",
    "current_successors_equal_clean_git_commit_blobs",
    "replacement_scope_is_complete_and_minimal",
    "cargo_metadata_locked_offline",
    "workspace_members_match_root_manifest",
    "hwpx_package_diagnostic_dev_edges_exact",
    "cargo_lock_contains_diagnostic_dev_edges",
    "canonical_receipt_written",
)
SOURCES = (
    "Cargo.toml",
    "Cargo.lock",
    "crates/hwpx-package/Cargo.toml",
    MAIN_CONTRACT,
    POSTGRES_CONTRACT,
    P15_CONTRACT,
    P15_AUTH_CONTRACT,
    WIDGET_CONTRACT,
    RETENTION_CONTRACT,
    "tools/p16/integrated_source_qualification.py",
    "tools/p17/run_current_workspace_source_checks.py",
    "tools/p17/tests/test_current_workspace_source_checks.py",
)


class AcceptanceError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise AcceptanceError(code)


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def executable(name: str) -> str:
    value = shutil.which(name)
    require(value is not None and Path(value).is_file(), "executable.missing")
    return value


def command(
    arguments: list[str],
    *,
    cwd: Path = ROOT,
    timeout: int = 120,
) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        [executable(arguments[0]), *arguments[1:]],
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        check=False,
        capture_output=True,
        timeout=timeout,
    )
    require(completed.returncode == 0, "command.failed")
    return completed


def bounded_file(root: Path, relative: str, maximum: int = 4_000_000) -> Path:
    require(
        isinstance(relative, str)
        and 0 < len(relative) <= 240
        and "\\" not in relative
        and ":" not in relative
        and "\0" not in relative,
        "path.shape",
    )
    value = PurePosixPath(relative)
    require(not value.is_absolute() and all(part not in ("", ".", "..") for part in value.parts), "path.escape")
    resolved_root = root.resolve(strict=True)
    cursor = resolved_root
    for part in value.parts:
        cursor /= part
        require(
            not cursor.is_symlink()
            and not (hasattr(cursor, "is_junction") and cursor.is_junction()),
            "path.link",
        )
    resolved = cursor.resolve(strict=True)
    require(resolved_root in resolved.parents and resolved.is_file(), "path.file")
    require(0 < resolved.stat().st_size <= maximum, "path.bound")
    return resolved


def load_json(path: Path, code: str) -> dict[str, Any]:
    require(path.is_file() and 0 < path.stat().st_size <= 512_000, f"{code}.file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AcceptanceError(f"{code}.parse") from error
    require(isinstance(value, dict), f"{code}.object")
    return value


def load_pinned_contracts(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for relative, expected in PINNED_CONTRACTS.items():
        path = bounded_file(root, relative, 512_000)
        require(digest(path) == expected, "predecessor.digest")
        result[relative] = load_json(path, "predecessor")
    return result


def add_expectation(
    expectations: dict[str, set[str]], relative: Any, expected: Any
) -> None:
    require(
        isinstance(relative, str)
        and isinstance(expected, str)
        and HEX.fullmatch(expected) is not None,
        "predecessor.source",
    )
    expectations.setdefault(relative, set()).add(expected)


def source_expectations(
    contracts: dict[str, dict[str, Any]],
) -> tuple[dict[str, set[str]], dict[str, tuple[str, str]]]:
    main = contracts[MAIN_CONTRACT]
    postgres = contracts[POSTGRES_CONTRACT]
    p15 = contracts[P15_CONTRACT]
    p15_auth = contracts[P15_AUTH_CONTRACT]
    widget = contracts[WIDGET_CONTRACT]
    retention = contracts[RETENTION_CONTRACT]
    expectations: dict[str, set[str]] = {}
    main_replacements: dict[str, tuple[str, str]] = {}
    for entry in main.get("replacements", []):
        require(isinstance(entry, dict), "main.replacement")
        relative = entry.get("path")
        before = entry.get("predecessor_sha256")
        after = entry.get("successor_sha256")
        add_expectation(expectations, relative, after)
        require(isinstance(relative, str) and isinstance(before, str), "main.replacement")
        main_replacements[relative] = (before, after)
    for entry in main.get("guard_sources", []):
        require(isinstance(entry, dict), "main.guard")
        add_expectation(expectations, entry.get("path"), entry.get("sha256"))
    for field in ("runtime_sources", "guard_sources"):
        for entry in postgres.get(field, []):
            require(isinstance(entry, dict), "postgres.source")
            add_expectation(expectations, entry.get("path"), entry.get("sha256"))
    contexts = p15.get("contexts")
    require(isinstance(contexts, dict), "p15.contexts")
    for entries in contexts.values():
        require(isinstance(entries, list), "p15.context")
        for entry in entries:
            require(isinstance(entry, dict), "p15.source")
            add_expectation(expectations, entry.get("path"), entry.get("successor_sha256"))
    for entry in p15.get("guard_sources", []):
        require(isinstance(entry, dict), "p15.guard")
        add_expectation(expectations, entry.get("path"), entry.get("sha256"))
    for entry in p15_auth.get("source_locks", []):
        require(isinstance(entry, dict), "p15_auth.source")
        add_expectation(expectations, entry.get("path"), entry.get("sha256"))
    for entry in widget.get("source_locks", []):
        require(isinstance(entry, dict), "widget.source")
        add_expectation(expectations, entry.get("path"), entry.get("sha256"))
    for entry in retention.get("source_files", []):
        require(isinstance(entry, dict), "retention.source")
        add_expectation(expectations, entry.get("path"), entry.get("sha256"))
    require(len(expectations) == len(set(expectations)), "predecessor.duplicates")
    for relative, baseline in PINNED_AMBIGUOUS_BASELINES.items():
        require(
            relative in expectations
            and len(expectations[relative]) > 1
            and baseline in expectations[relative],
            "predecessor.pinned_baseline",
        )
    return expectations, main_replacements


def git_blob_digest(root: Path, revision: str, relative: str) -> str:
    completed = command(["git", "show", f"{revision}:{relative}"], cwd=root, timeout=30)
    require(0 < len(completed.stdout) <= 4_000_000, "git.blob_bound")
    return digest_bytes(completed.stdout)


def current_source_entries(root: Path, commit: str) -> list[dict[str, Any]]:
    contracts = load_pinned_contracts(root)
    expectations, main_replacements = source_expectations(contracts)
    entries: list[dict[str, Any]] = []
    for relative in sorted(expectations):
        current = digest(bounded_file(root, relative))
        if relative in main_replacements:
            baseline = main_replacements[relative][1]
        else:
            if current in expectations[relative]:
                continue
            baseline = PINNED_AMBIGUOUS_BASELINES.get(relative)
            if baseline is None:
                require(len(expectations[relative]) == 1, "predecessor.ambiguous")
                baseline = next(iter(expectations[relative]))
            else:
                require(baseline in expectations[relative], "predecessor.pinned_baseline")
        if current == baseline:
            continue
        require(git_blob_digest(root, commit, relative) == current, "git.current_blob")
        composition = (
            main_replacements[relative][0]
            if relative in main_replacements
            else baseline
        )
        accepted = set(expectations[relative])
        accepted.add(composition)
        entries.append(
            {
                "path": relative,
                "accepted_predecessor_sha256s": sorted(accepted),
                "composition_predecessor_sha256": composition,
                "current_sha256": current,
            }
        )
    require(len(entries) == len({entry["path"] for entry in entries}), "successor.duplicates")
    return entries


def cargo_projection(root: Path) -> tuple[str, int]:
    completed = command(
        ["cargo", "metadata", "--locked", "--offline", "--format-version", "1", "--no-deps"],
        cwd=root,
        timeout=120,
    )
    try:
        metadata = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AcceptanceError("cargo.metadata") from error
    require(isinstance(metadata, dict), "cargo.metadata")
    packages = metadata.get("packages")
    members = metadata.get("workspace_members")
    require(isinstance(packages, list) and isinstance(members, list), "cargo.metadata_shape")
    member_ids = set(members)
    projection = []
    names: set[str] = set()
    for package in packages:
        require(isinstance(package, dict), "cargo.package")
        if package.get("id") not in member_ids:
            continue
        name = package.get("name")
        version = package.get("version")
        manifest = package.get("manifest_path")
        require(
            isinstance(name, str)
            and name not in names
            and isinstance(version, str)
            and isinstance(manifest, str),
            "cargo.package_identity",
        )
        names.add(name)
        manifest_path = Path(manifest).resolve(strict=True)
        try:
            manifest_relative = manifest_path.relative_to(root.resolve(strict=True)).as_posix()
        except ValueError as error:
            raise AcceptanceError("cargo.manifest_escape") from error
        dependencies = package.get("dependencies")
        require(isinstance(dependencies, list), "cargo.dependencies")
        projection.append(
            {
                "name": name,
                "version": version,
                "manifest": manifest_relative,
                "dependencies": sorted(
                    [
                        {
                        "name": dependency.get("name"),
                        "kind": dependency.get("kind"),
                        "req": dependency.get("req"),
                        }
                        for dependency in dependencies
                        if isinstance(dependency, dict)
                    ],
                    key=lambda value: (
                        str(value["name"]),
                        str(value["kind"]),
                        str(value["req"]),
                    ),
                ),
            }
        )
    root_manifest = tomllib.loads((root / "Cargo.toml").read_text(encoding="utf-8"))
    declared_members = root_manifest.get("workspace", {}).get("members")
    require(isinstance(declared_members, list), "cargo.workspace_members")
    require(
        {entry["manifest"].removesuffix("/Cargo.toml") for entry in projection}
        == set(declared_members),
        "cargo.workspace_member_mismatch",
    )
    hwpx_manifest = tomllib.loads(
        (root / "crates/hwpx-package/Cargo.toml").read_text(encoding="utf-8")
    )
    dev = hwpx_manifest.get("dev-dependencies")
    require(
        isinstance(dev, dict)
        and dev.get("serde") == {"workspace": True}
        and dev.get("serde_json") == {"workspace": True},
        "cargo.hwpx_diagnostic_edges",
    )
    lock = tomllib.loads((root / "Cargo.lock").read_text(encoding="utf-8"))
    lock_packages = lock.get("package")
    require(isinstance(lock_packages, list), "cargo.lock_packages")
    hwpx_locks = [item for item in lock_packages if isinstance(item, dict) and item.get("name") == "hwpx-package"]
    require(len(hwpx_locks) == 1, "cargo.lock_hwpx")
    lock_dependencies = hwpx_locks[0].get("dependencies")
    require(
        isinstance(lock_dependencies, list)
        and "serde" in lock_dependencies
        and "serde_json" in lock_dependencies,
        "cargo.lock_diagnostic_edges",
    )
    return digest_bytes(canonical(sorted(projection, key=lambda value: value["name"]))), len(projection)


def tracked_identity(root: Path) -> tuple[str, bool]:
    commit = command(["git", "rev-parse", "HEAD"], cwd=root, timeout=30).stdout.decode("ascii").strip()
    require(bool(re.fullmatch(r"[0-9a-f]{40}", commit)), "git.commit")
    status = command(
        ["git", "status", "--porcelain", "--untracked-files=no"], cwd=root, timeout=30
    ).stdout
    return commit, status == b""


def run() -> dict[str, Any]:
    commit, clean = tracked_identity(ROOT)
    require(clean, "git.dirty")
    entries = current_source_entries(ROOT, commit)
    require(entries, "successor.empty")
    metadata_sha256, member_count = cargo_projection(ROOT)
    require(tracked_identity(ROOT) == (commit, True), "git.changed")
    run_id = uuid.uuid4().hex
    run_dir = RUNS / run_id
    require(not run_dir.exists(), "receipt.exists")
    run_dir.mkdir(parents=True)
    receipt = {
        "schema_version": "hwpx-agent.p17-current-workspace-source-check/v1",
        "run_id": run_id,
        "scope": "current_pc_source_binding_successor_only",
        "source_commit": commit,
        "checks": list(CHECKS),
        "check_count": len(CHECKS),
        "passed": True,
        "decision": "PASS",
        "predecessor_contract_sha256": PINNED_CONTRACTS,
        "successors": entries,
        "successor_count": len(entries),
        "cargo_metadata_projection_sha256": metadata_sha256,
        "cargo_workspace_member_count": member_count,
        "actual_hangul": False,
        "registered_host": False,
        "production": False,
        "other_pc_or_version": False,
        "phase_complete": False,
    }
    path = run_dir / "receipt.json"
    path.write_bytes(canonical(receipt))
    require(path.read_bytes() == canonical(receipt), "receipt.canonical")
    return receipt


if __name__ == "__main__":
    try:
        result = run()
    except (AcceptanceError, OSError, subprocess.SubprocessError, tomllib.TOMLDecodeError) as error:
        code = str(error) if isinstance(error, AcceptanceError) else "acceptance.unavailable"
        print(json.dumps({"decision": "FAIL", "code": code}, sort_keys=True))
        raise SystemExit(1) from None
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "run_id": result["run_id"],
                "check_count": result["check_count"],
                "successor_count": result["successor_count"],
            },
            sort_keys=True,
        )
    )
