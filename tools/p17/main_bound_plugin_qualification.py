"""Freeze and verify the integrated-main personal plugin binding."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import run_main_bound_plugin_checks as host_checks


ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION = ROOT / "implementation/p17/qualification/main-bound-plugin-v2-20260906"
RUN_ID = "890e1150a2184172abbe8af0ef3eb7b2"
BASE_COMMIT = "0f408de00620bf4227a124e6a14c5fc6fe04fc08"
RECEIPT_SHA256 = "61d60800a2a86277ccc215f3f6d2a92f1fb97f2101a841667e39fe7da04b5cbd"
THREAD_ID = "01a0744d-0c14-7573-ab9a-175f545c1ce2"
EXTERNAL_HASHES = {
    "manifest_sha256": "6d9d364017333ce084425b81e230a9abde12c1f709b2c764b782000a53938fce",
    "mcp_sha256": "1481ea604f322b054345826a961e269871f2963602f63037d0f72bc2945bbb1f",
    "runtime_sha256": "b1a294a5a250f4209db63a76ac98b7d44a1abda345121373cca422eb4577c6e2",
}
CLAIMS = {
    "integrated_main_root": True,
    "actual_codex_plugin": True,
    "actual_codex_health_call": True,
    "cachebuster_reinstall": True,
    "persistent_credentials": False,
    "postgres_lifecycle": False,
    "actual_hangul": False,
    "product_network_enabled": False,
    "codex_service_used": True,
    "phase_complete": False,
}
RUNTIME_SOURCES = (
    "Cargo.toml",
    "Cargo.lock",
    "pnpm-lock.yaml",
    "crates/local-companion-daemon/src/lib.rs",
    "crates/local-companion-daemon/src/main.rs",
    "protocol/private/p17-local-daemon-v1.json",
    "protocol/private/p17-local-mcp-v1.json",
    "web/local-companion-mcp/package.json",
    "web/local-companion-mcp/src/server.ts",
    "web/local-companion-mcp/src/server.test.ts",
    "tools/p17/run_personal_plugin_checks.py",
    "tools/p17/run_main_bound_plugin_checks.py",
    "tools/p17/tests/test_main_bound_plugin_checks.py",
)
GUARD_SOURCES = (
    "tools/p17/main_bound_plugin_qualification.py",
    "tools/p17/tests/test_main_bound_plugin_qualification.py",
    "implementation/p17/P17-04_MAIN_BINDING_V2.md",
)


class QualificationError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(document: object) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def load_document(path: Path, code: str) -> dict[str, Any]:
    require(path.is_file() and 0 < path.stat().st_size <= 256_000, f"{code}.file")
    try:
        raw = path.read_bytes()
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError(f"{code}.parse") from error
    require(isinstance(document, dict), f"{code}.type")
    require(raw == canonical(document), f"{code}.canonical")
    return document


def source_lock(root: Path, relative: str) -> dict[str, object]:
    path = root / relative
    require(path.is_file(), "source.missing")
    return {"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)}


def expected_receipt() -> dict[str, Any]:
    return {
        "actual_codex_plugin": True,
        "actual_hangul": False,
        "check_count": len(host_checks.CHECKS),
        "checks": list(host_checks.CHECKS),
        "codex_service_used": True,
        "decision": "PASS",
        "ephemeral_codex_thread_id": THREAD_ID,
        "external_config_hashes": EXTERNAL_HASHES,
        "health_config_sha256": EXTERNAL_HASHES["runtime_sha256"],
        "main_root_bound": True,
        "passed": True,
        "plugin_id": "hwpx-agent-local@personal",
        "plugin_version": host_checks.PLUGIN_VERSION,
        "product_network_enabled": False,
        "run_id": RUN_ID,
        "schema_version": "hwpx-agent.p17-main-bound-plugin-check/v1",
        "scope": "current_pc_integrated_main_personal_plugin_health_only",
        "source_commit": BASE_COMMIT,
        "tracked_clean": True,
    }


def validate_receipt(receipt: dict[str, Any]) -> None:
    expected = expected_receipt()
    require(set(receipt) == set(expected), "receipt.fields")
    require(receipt == expected, "receipt.claims")


def receipt_path(root: Path) -> Path:
    return root / "artifacts/p17/main-bound-plugin-runs" / RUN_ID / "receipt.json"


def qualify() -> tuple[Path, Path]:
    path = receipt_path(ROOT)
    receipt = load_document(path, "receipt")
    validate_receipt(receipt)
    require(digest(path) == RECEIPT_SHA256, "receipt.digest")
    require(host_checks.validate_main_binding() == EXTERNAL_HASHES, "host_state")
    runtime_locks = [source_lock(ROOT, relative) for relative in RUNTIME_SOURCES]
    current = {
        "schema_version": "hwpx-agent.p17-main-bound-plugin-current/v1",
        "scope": receipt["scope"],
        "run_id": RUN_ID,
        "source_commit": BASE_COMMIT,
        "plugin_id": receipt["plugin_id"],
        "plugin_version": receipt["plugin_version"],
        "ephemeral_codex_thread_id": THREAD_ID,
        "checks": list(host_checks.CHECKS),
        "external_config_hashes": EXTERNAL_HASHES,
        "claims": CLAIMS,
        "receipt": {
            "path": receipt_path(ROOT).relative_to(ROOT).as_posix(),
            "sha256": RECEIPT_SHA256,
        },
        "source_hashes": {entry["path"]: entry["sha256"] for entry in runtime_locks},
    }
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(canonical(current))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


def expected_contract(root: Path, current_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-main-bound-plugin-qualification/v1",
        "qualification_id": "p17.main-bound-plugin.v2.20260906",
        "base_commit": BASE_COMMIT,
        "scope": "current_pc_integrated_main_plugin_successor_only",
        "claims": CLAIMS,
        "evidence": {
            "path": (
                "implementation/p17/qualification/"
                "main-bound-plugin-v2-20260906/current-host.json"
            ),
            "canonical_sha256": digest(current_path),
            "run_id": RUN_ID,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "runtime_sources": [source_lock(root, relative) for relative in RUNTIME_SOURCES],
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
    }


def verify(root: Path = ROOT) -> dict[str, Any]:
    directory = root / QUALIFICATION.relative_to(ROOT)
    current_path = directory / "current-host.json"
    contract_path = directory / "contract.json"
    current = load_document(current_path, "current")
    contract = load_document(contract_path, "contract")
    require(
        current.get("schema_version") == "hwpx-agent.p17-main-bound-plugin-current/v1"
        and current.get("scope") == "current_pc_integrated_main_personal_plugin_health_only"
        and current.get("run_id") == RUN_ID
        and current.get("source_commit") == BASE_COMMIT
        and current.get("plugin_id") == "hwpx-agent-local@personal"
        and current.get("plugin_version") == host_checks.PLUGIN_VERSION
        and current.get("ephemeral_codex_thread_id") == THREAD_ID
        and current.get("checks") == list(host_checks.CHECKS)
        and current.get("external_config_hashes") == EXTERNAL_HASHES
        and current.get("claims") == CLAIMS
        and current.get("receipt")
        == {
            "path": f"artifacts/p17/main-bound-plugin-runs/{RUN_ID}/receipt.json",
            "sha256": RECEIPT_SHA256,
        },
        "current.exact",
    )
    runtime_locks = [source_lock(root, relative) for relative in RUNTIME_SOURCES]
    require(
        current.get("source_hashes")
        == {entry["path"]: entry["sha256"] for entry in runtime_locks},
        "current.sources",
    )
    require(contract == expected_contract(root, current_path), "contract.exact")
    return contract


def verify_host() -> None:
    verify()
    require(host_checks.validate_main_binding() == EXTERNAL_HASHES, "host_state")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: main_bound_plugin_qualification.py RUN_ID|verify|verify-host")
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_MAIN_BOUND_PLUGIN_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_MAIN_BOUND_PLUGIN_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    elif sys.argv[1] == "verify-host":
        verify_host()
        print("P17_MAIN_BOUND_PLUGIN_HOST_VERIFY_PASS")
    else:
        raise SystemExit("usage: main_bound_plugin_qualification.py RUN_ID|verify|verify-host")
