"""Exact P15 source successor for composed P16 work; never a phase or production waiver."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p16/qualification/p15-current-source-v1"
CONTRACT_PATH = f"{BASE}/contract.json"
POSTGRES_CONTRACT = "implementation/p16/qualification/postgres-217ba56/contract.json"
POSTGRES_CONTRACT_SHA256 = "c37e5b773a9117ffdb4af40c95d1263e08fdf7f6e25c69c6daa3108086497530"
P14_CANCEL_CONTRACT = "implementation/p14/postgres/p14-cancel-cleanup-v1.json"
P14_CANCEL_CONTRACT_SHA256 = "ee5b6f1180d1c2cc0363a5dae911647f5dc6f8ea536722baf61d04b76a23d291"
P15_ARTIFACT_CONTRACT = "implementation/p15/p15-artifact-delivery-contract-v1.json"
P15_ARTIFACT_CONTRACT_SHA256 = "df025b658d49991f80b392a8afa693c412ef14ad5e90c770356956405c7e42a5"
P15_AUTH_CONTRACT = "implementation/p15/p15-auth-tenant-v1.json"
P15_AUTH_CONTRACT_SHA256 = "7bae38b349e394b53636462fe19cb8e1c057a35ab68e7c23161086af6400ad99"
P15_ASYNC_CONTRACT = "implementation/p15/p15-async-job-contract-v1.json"
P15_ASYNC_CONTRACT_SHA256 = "311e9272373da0129693ad87c8a42e1e6c56b17b34ccb1312eed630b7f049c32"
P15_ERROR_CONTRACT = "implementation/p15/p15-error-mapping-contract-v1.json"
P15_ERROR_CONTRACT_SHA256 = "ae33d499350ca53f55534744036fc5830e4748efe943482b90c9e063bf54bd8b"
P15_HANDLER_CONTRACT = "implementation/p15/p15-handler-contract-v1.json"
P15_HANDLER_CONTRACT_SHA256 = "f79dfeac599b11a122569e1796d428298f341f53f91d3893460c6d7c1d704f0a"
P15_INSPECTOR_CONTRACT = "implementation/p15/p15-inspector-staging-contract-v1.json"
P15_INSPECTOR_CONTRACT_SHA256 = "09335ea42021c782f75010d7e873de11c36c834bb33ba8cafde529f824e3b907"
P15_TELEMETRY_CONTRACT = "implementation/p15/p15-telemetry-contract-v1.json"
P15_TELEMETRY_CONTRACT_SHA256 = "9a0e32959a6129f316f609069e87e22f22fb68b11622935c7ca32c080f44e402"
P15_QUOTA_CONTRACT = "implementation/p15/p15-quota-contract-v1.json"
P15_QUOTA_CONTRACT_SHA256 = "787f88e79b0b1aa1dff483237cf60e9a30526ab686481ec779fe04a3cd3db872"
P16_WIDGET_CONTRACT = "implementation/p16/p16-widget-shell-contract-v1.json"
P16_WIDGET_CONTRACT_SHA256 = "2d8dad6318bc9090b0a7db70d19f1470e6ce0fa97bb177755cff993f9b94f09e"
P15_ARTIFACT_REVISION = "dde79ff3fa86953c7f3e6e8e2402479eddee813e"
P14_CANCEL_REVISION = "8d03bb6b4fb69e73f8921aa26484b400dadf941b"
P15_AUTH_REVISION = "8ac8d74a0f7795315d2dc2e0573f6b9a3a4e11e9"
P15_ASYNC_REVISION = "4c6224f6001c5daadaaaec907c0bba86db7c6c0f"
P15_ERROR_REVISION = "f36a07e988558b4481c50955a0f76bd69c516d9d"
P15_HANDLER_REVISION = "9e7ed73524be0049292fbdf45f2170df6f997fae"
P15_INSPECTOR_REVISION = "7ea2f84c244fe5bbd7926ba3f176dc5acafcf624"
P15_TELEMETRY_REVISION = "9f9c6932518175906842a2cbb5915a0fb96d0d49"
P15_QUOTA_REVISION = "e15921a59d45056c46b8ae94b6f6af778746c534"
P16_WIDGET_REVISION = "19d1cf775e5702e1150e35624bf616f1dbf9a34c"
P16_PLAN_AUTH_REVISION = "9c120ac7407c00a7454a195c403330b47ff0524f"
P16_POSTGRES_REVISION = "217ba56cd8a88e4d3560a5735052b18880481ff4"
HEX = re.compile(r"[0-9a-f]{64}\Z")

POSTGRES_PATHS = (
    "Cargo.toml",
    "Cargo.lock",
    "crates/artifact-service/Cargo.toml",
    "crates/artifact-service/src/lib.rs",
    "crates/artifact-service/src/service.rs",
    "crates/artifact-service/src/store.rs",
)
PLAN_AUTH_PATHS = (
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/policy.rs",
)
ARTIFACT_PATHS = POSTGRES_PATHS + PLAN_AUTH_PATHS
AUTH_PATHS = ("tools/p14/validate_cancel_cleanup.py",)
ASYNC_PATHS = ("crates/mcp-control-plane/src/policy.rs",)
CANCEL_PATHS = ("crates/artifact-service/src/store.rs",)
ERROR_PATHS = (
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/src/policy.rs",
)
HANDLER_PATHS = (
    "crates/mcp-control-plane/src/policy.rs",
    "tools/p15/validate_auth_tenant.py",
)
INSPECTOR_PATHS = (
    "Cargo.toml",
    "Cargo.lock",
    "tools/p15/validate_artifact_delivery_contract.py",
    "tools/p15/validate_async_job_contract.py",
    "tools/p15/validate_error_mapping_contract.py",
    "tools/p15/validate_handler_contract.py",
    "tools/p15/validate_quota_contract.py",
    "tools/p15/validate_telemetry_contract.py",
    "tools/p15/validate_inspector_staging_contract.py",
)
TELEMETRY_PATHS = PLAN_AUTH_PATHS
QUOTA_PATHS = ERROR_PATHS
WIDGET_PATHS = (
    "tools/p15/validate_inspector_staging_contract.py",
    "tools/p16/build_widget_shell_contract.py",
)
GUARD_PATHS = (
    "tools/p16/p15_source_qualification.py",
    "tools/p16/validate_widget_shell_successor.py",
    "tools/p16/build_widget_shell_contract.py",
    "tools/p16/tests/test_p15_source_qualification.py",
    "tools/p15/validate_artifact_delivery_contract.py",
    "tools/p15/validate_async_job_contract.py",
    "tools/p15/validate_error_mapping_contract.py",
    "tools/p15/validate_handler_contract.py",
    "tools/p15/validate_quota_contract.py",
    "tools/p15/validate_telemetry_contract.py",
    "tools/p15/validate_inspector_staging_contract.py",
    "tools/p15/validate_auth_tenant.py",
    "tools/p14/validate_cancel_cleanup.py",
    "implementation/p16/P16-06_P15_SOURCE_QUALIFICATION.md",
)
_VERIFIED_CACHE: dict[tuple[str, str], dict[str, dict[str, tuple[str, str]]]] = {}


class QualificationError(ValueError):
    """Closed qualification failure with no candidate data in its message."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_postgres_validator() -> Any:
    path = Path(__file__).resolve().parent / "postgres_artifact_qualification.py"
    specification = importlib.util.spec_from_file_location("p16_postgres_qualification_for_p15", path)
    require(specification is not None and specification.loader is not None, "postgres.validator")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def pinned_object(postgres: Any, root: Path, relative: str, expected_hash: str) -> dict[str, Any]:
    raw = postgres.read_bounded(root, relative)
    require(digest(raw) == expected_hash, "predecessor.digest")
    value = postgres.json_value(raw)
    require(isinstance(value, dict), "predecessor.object")
    return value


def source_locks(contract: dict[str, Any], field: str = "source_locks") -> dict[str, str]:
    values = contract.get(field)
    require(isinstance(values, list), "predecessor.sources")
    result: dict[str, str] = {}
    for entry in values:
        require(isinstance(entry, dict) and set(entry) == {"path", "sha256"}, "predecessor.source")
        relative = entry["path"]
        expected = entry["sha256"]
        require(isinstance(relative, str) and relative not in result, "predecessor.source_path")
        require(isinstance(expected, str) and HEX.fullmatch(expected) is not None, "predecessor.source_hash")
        result[relative] = expected
    return result


def source_at_revision(root: Path, revision: str, relative: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{revision}:{relative}"], cwd=root, check=False, capture_output=True
    )
    require(result.returncode == 0 and 0 < len(result.stdout) <= 4_000_000, "history.source")
    return digest(result.stdout)


def replacement_list(
    postgres: Any,
    root: Path,
    paths: tuple[str, ...],
    predecessor: dict[str, str],
    successors: dict[str, str],
    predecessor_revision: str,
) -> list[dict[str, str]]:
    result = []
    for relative in paths:
        require(relative in predecessor and relative in successors, "replacement.path")
        before = predecessor[relative]
        after = successors[relative]
        require(before != after, "replacement.unchanged")
        require(source_at_revision(root, predecessor_revision, relative) == before, "history.predecessor")
        require(digest(postgres.read_bounded(root, relative)) == after, "replacement.successor")
        result.append({"path": relative, "predecessor_sha256": before, "successor_sha256": after})
    return result


def expected_contract(root: Path) -> dict[str, Any]:
    postgres = load_postgres_validator()
    postgres.verified_replacements(root)
    postgres_contract = pinned_object(postgres, root, POSTGRES_CONTRACT, POSTGRES_CONTRACT_SHA256)
    runtime_entries = postgres_contract.get("runtime_sources")
    require(isinstance(runtime_entries, list), "postgres.runtime_sources")
    runtime: dict[str, str] = {}
    for entry in runtime_entries:
        require(isinstance(entry, dict) and set(entry) == {"path", "sha256"}, "postgres.runtime_source")
        require(entry["path"] not in runtime and HEX.fullmatch(entry["sha256"]) is not None,
                "postgres.runtime_source")
        runtime[entry["path"]] = entry["sha256"]
    require(all(relative in runtime for relative in POSTGRES_PATHS), "postgres.runtime_missing")

    cancel_contract = pinned_object(postgres, root, P14_CANCEL_CONTRACT, P14_CANCEL_CONTRACT_SHA256)
    artifact_contract = pinned_object(
        postgres, root, P15_ARTIFACT_CONTRACT, P15_ARTIFACT_CONTRACT_SHA256
    )
    auth_contract = pinned_object(postgres, root, P15_AUTH_CONTRACT, P15_AUTH_CONTRACT_SHA256)
    async_contract = pinned_object(postgres, root, P15_ASYNC_CONTRACT, P15_ASYNC_CONTRACT_SHA256)
    error_contract = pinned_object(postgres, root, P15_ERROR_CONTRACT, P15_ERROR_CONTRACT_SHA256)
    handler_contract = pinned_object(postgres, root, P15_HANDLER_CONTRACT, P15_HANDLER_CONTRACT_SHA256)
    inspector_contract = pinned_object(
        postgres, root, P15_INSPECTOR_CONTRACT, P15_INSPECTOR_CONTRACT_SHA256
    )
    telemetry_contract = pinned_object(
        postgres, root, P15_TELEMETRY_CONTRACT, P15_TELEMETRY_CONTRACT_SHA256
    )
    quota_contract = pinned_object(postgres, root, P15_QUOTA_CONTRACT, P15_QUOTA_CONTRACT_SHA256)
    widget_contract = pinned_object(postgres, root, P16_WIDGET_CONTRACT, P16_WIDGET_CONTRACT_SHA256)
    cancel_before = source_locks(cancel_contract, "source_files")
    artifact_before = source_locks(artifact_contract)
    auth_before = source_locks(auth_contract)
    async_before = source_locks(async_contract)
    error_before = source_locks(error_contract)
    handler_before = source_locks(handler_contract)
    inspector_before = source_locks(inspector_contract)
    telemetry_before = source_locks(telemetry_contract)
    quota_before = source_locks(quota_contract)
    widget_before = source_locks(widget_contract)

    successors = {relative: runtime[relative] for relative in POSTGRES_PATHS}
    for relative in PLAN_AUTH_PATHS:
        current = digest(postgres.read_bounded(root, relative))
        require(source_at_revision(root, P16_PLAN_AUTH_REVISION, relative) == current, "history.plan_auth")
        successors[relative] = current
    for relative in GUARD_PATHS:
        successors[relative] = digest(postgres.read_bounded(root, relative))

    contexts = {
        "p15_artifact": replacement_list(
            postgres, root, ARTIFACT_PATHS, artifact_before, successors, P15_ARTIFACT_REVISION
        ),
        "p15_auth": replacement_list(
            postgres, root, AUTH_PATHS, auth_before, successors, P15_AUTH_REVISION
        ),
        "p15_async": replacement_list(
            postgres, root, ASYNC_PATHS, async_before, successors, P15_ASYNC_REVISION
        ),
        "p14_cancel": replacement_list(
            postgres, root, CANCEL_PATHS, cancel_before, successors, P14_CANCEL_REVISION
        ),
        "p15_error": replacement_list(
            postgres, root, ERROR_PATHS, error_before, successors, P15_ERROR_REVISION
        ),
        "p15_handler": replacement_list(
            postgres, root, HANDLER_PATHS, handler_before, successors, P15_HANDLER_REVISION
        ),
        "p15_inspector": replacement_list(
            postgres, root, INSPECTOR_PATHS, inspector_before, successors, P15_INSPECTOR_REVISION
        ),
        "p15_telemetry": replacement_list(
            postgres, root, TELEMETRY_PATHS, telemetry_before, successors, P15_TELEMETRY_REVISION
        ),
        "p15_quota": replacement_list(
            postgres, root, QUOTA_PATHS, quota_before, successors, P15_QUOTA_REVISION
        ),
        "p16_widget": replacement_list(
            postgres, root, WIDGET_PATHS, widget_before, successors, P16_WIDGET_REVISION
        ),
    }
    return {
        "schema_version": "hwpx-agent.p16-p15-source-qualification/v1",
        "qualification_id": "p16.composed_current_source.p15.v1",
        "scope": "current_pc_source_binding_successor_only",
        "audited_runtime_commits": {
            "p16_plan_authorization": P16_PLAN_AUTH_REVISION,
            "p16_postgres_adapter": P16_POSTGRES_REVISION,
        },
        "predecessors": [
            {"path": P14_CANCEL_CONTRACT, "sha256": P14_CANCEL_CONTRACT_SHA256},
            {"path": P15_ARTIFACT_CONTRACT, "sha256": P15_ARTIFACT_CONTRACT_SHA256},
            {"path": P15_AUTH_CONTRACT, "sha256": P15_AUTH_CONTRACT_SHA256},
            {"path": P15_ASYNC_CONTRACT, "sha256": P15_ASYNC_CONTRACT_SHA256},
            {"path": P15_ERROR_CONTRACT, "sha256": P15_ERROR_CONTRACT_SHA256},
            {"path": P15_HANDLER_CONTRACT, "sha256": P15_HANDLER_CONTRACT_SHA256},
            {"path": P15_INSPECTOR_CONTRACT, "sha256": P15_INSPECTOR_CONTRACT_SHA256},
            {"path": P15_QUOTA_CONTRACT, "sha256": P15_QUOTA_CONTRACT_SHA256},
            {"path": P15_TELEMETRY_CONTRACT, "sha256": P15_TELEMETRY_CONTRACT_SHA256},
            {"path": P16_WIDGET_CONTRACT, "sha256": P16_WIDGET_CONTRACT_SHA256},
            {"path": POSTGRES_CONTRACT, "sha256": POSTGRES_CONTRACT_SHA256},
        ],
        "contexts": contexts,
        "guard_sources": [
            {"path": relative, "sha256": successors[relative]} for relative in GUARD_PATHS
        ],
        "claims": {
            "source_qualification_only": True,
            "p15_phase_retested": False,
            "p16_phase_complete": False,
            "actual_hangul": False,
            "registered_host": False,
            "production": False,
            "other_pc_or_version": False,
        },
    }


def verification_fingerprint(root: Path) -> str:
    postgres = load_postgres_validator()
    paths = set(postgres.RUNTIME_PATHS) | set(postgres.GUARD_PATHS) | {
        postgres.PREDECESSOR_PATH,
        postgres.CONTRACT_PATH,
        f"{postgres.BASE}/current-db.json",
        f"{postgres.BASE}/independent-db.json",
        CONTRACT_PATH,
        P15_ARTIFACT_CONTRACT,
        P14_CANCEL_CONTRACT,
        P15_AUTH_CONTRACT,
        P15_ASYNC_CONTRACT,
        P15_ERROR_CONTRACT,
        P15_HANDLER_CONTRACT,
        P15_INSPECTOR_CONTRACT,
        P15_QUOTA_CONTRACT,
        P15_TELEMETRY_CONTRACT,
        P16_WIDGET_CONTRACT,
        *PLAN_AUTH_PATHS,
        *GUARD_PATHS,
    }
    state = hashlib.sha256()
    for relative in sorted(paths):
        raw = postgres.read_bounded(root, relative)
        state.update(relative.encode("utf-8"))
        state.update(b"\0")
        state.update(hashlib.sha256(raw).digest())
    return state.hexdigest()


def verified_contexts(root: Path) -> dict[str, dict[str, tuple[str, str]]]:
    try:
        key = (str(root.resolve(strict=True)), verification_fingerprint(root))
        cached = _VERIFIED_CACHE.get(key)
        if cached is not None:
            return cached
        postgres = load_postgres_validator()
        contract = postgres.json_value(postgres.read_bounded(root, CONTRACT_PATH, 128 * 1024))
        expected = expected_contract(root)
        require(postgres.exact(contract, expected), "contract.exact")
        contexts = {
            name: {
                entry["path"]: (entry["predecessor_sha256"], entry["successor_sha256"])
                for entry in values
            }
            for name, values in expected["contexts"].items()
        }
        if len(_VERIFIED_CACHE) >= 8:
            _VERIFIED_CACHE.clear()
        _VERIFIED_CACHE[key] = contexts
        return contexts
    except (OSError, KeyError, TypeError, RecursionError) as error:
        raise QualificationError("qualification.unavailable") from error


def verified_context(root: Path, name: str) -> dict[str, tuple[str, str]]:
    contexts = verified_contexts(root)
    values = contexts.get(name)
    require(values is not None, "contract.context")
    return dict(values)


def verified_artifact_replacements(root: Path) -> dict[str, tuple[str, str]]:
    return verified_context(root, "p15_artifact")


def verified_auth_replacements(root: Path) -> dict[str, tuple[str, str]]:
    return verified_context(root, "p15_auth")


def verified_cancel_replacements(root: Path) -> dict[str, tuple[str, str]]:
    return verified_context(root, "p14_cancel")


def verified_async_replacements(root: Path) -> dict[str, tuple[str, str]]:
    return verified_context(root, "p15_async")


def verified_error_replacements(root: Path) -> dict[str, tuple[str, str]]:
    return verified_context(root, "p15_error")


def verified_handler_replacements(root: Path) -> dict[str, tuple[str, str]]:
    return verified_context(root, "p15_handler")


def verified_inspector_replacements(root: Path) -> dict[str, tuple[str, str]]:
    return verified_context(root, "p15_inspector")


def verified_telemetry_replacements(root: Path) -> dict[str, tuple[str, str]]:
    return verified_context(root, "p15_telemetry")


def verified_quota_replacements(root: Path) -> dict[str, tuple[str, str]]:
    return verified_context(root, "p15_quota")


def verified_widget_replacements(root: Path) -> dict[str, tuple[str, str]]:
    return verified_context(root, "p16_widget")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.write:
            expected = expected_contract(ROOT)
            destination = ROOT / CONTRACT_PATH
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write((json.dumps(expected, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        replacements = verified_artifact_replacements(ROOT)
        auth_replacements = verified_auth_replacements(ROOT)
        cancel_replacements = verified_cancel_replacements(ROOT)
        async_replacements = verified_async_replacements(ROOT)
        error_replacements = verified_error_replacements(ROOT)
        handler_replacements = verified_handler_replacements(ROOT)
        inspector = verified_inspector_replacements(ROOT)
        quota = verified_quota_replacements(ROOT)
        telemetry = verified_telemetry_replacements(ROOT)
        widget = verified_widget_replacements(ROOT)
    except (QualificationError, OSError, KeyError, TypeError) as error:
        code = str(error) if isinstance(error, QualificationError) else "qualification.unavailable"
        print(json.dumps({"decision": "FAIL", "code": code}, sort_keys=True))
        return 1
    print(json.dumps({
        "decision": "PASS", "scope": "source_binding_successor_only",
        "artifact_replacements": len(replacements), "auth_replacements": len(auth_replacements),
        "cancel_replacements": len(cancel_replacements), "async_replacements": len(async_replacements),
        "error_replacements": len(error_replacements), "handler_replacements": len(handler_replacements),
        "inspector_replacements": len(inspector), "quota_replacements": len(quota),
        "telemetry_replacements": len(telemetry), "widget_replacements": len(widget),
        "phase_complete": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
