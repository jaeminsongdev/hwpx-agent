"""Freeze and verify the P17-04 local MCP and personal-plugin qualification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import run_personal_plugin_checks as plugin_checks


ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION = ROOT / "implementation/p17/qualification/local-mcp-plugin-v1-20260906"
BRIDGE_RUN_ID = "d1a376b7563c4654b15fccbaa98645e0"
BRIDGE_COMMIT = "62844aef98cb114e08ac2e394ef5fbad32565bbb"
BRIDGE_RECEIPT_SHA256 = "c6ca18e2ad30454850b53284227f23abed10871e1ce532a633b8279550817c3e"
PLUGIN_RUN_ID = "273f6ccaac644836814b87679ab4eb0c"
PLUGIN_COMMIT = "e942e000be88894c70150af3a266bb892be8fa9e"
PLUGIN_RECEIPT_SHA256 = "c421cfcefc0157ad2eea1b6d3cb7f8bf0bdb6931b2fe630d2857ede6ce6ec332"
PLUGIN_THREAD_ID = "01a07443-f74c-7a51-a897-5f6ca89a5d45"
EXTERNAL_HASHES = {
    "manifest_sha256": "e85fa70d28c1d94392de459d06f3b2dcc04dae67efdec1dc09daeae6f7d3f33b",
    "mcp_sha256": "6646cc4092b8aabc38d9c1657dc6c45b1cf18373f239ed0ad75809cbbaa31e46",
    "runtime_sha256": "b1a294a5a250f4209db63a76ac98b7d44a1abda345121373cca422eb4577c6e2",
}
BRIDGE_CHECKS = (
    "clean_tracked_source",
    "locked_offline_rust_and_node_builds",
    "modern_stdio_mcp_initialized",
    "exactly_one_health_tool_discovered",
    "strict_empty_input_schema",
    "authenticated_daemon_health_called",
    "bounded_redacted_health_returned",
    "unknown_tool_argument_rejected",
    "private_paths_and_document_content_absent",
    "graceful_stdio_shutdown",
    "temporary_resources_cleaned",
    "no_hangul_or_network_used",
)
PLUGIN_CHECKS = plugin_checks.CHECKS
CLAIMS = {
    "local_stdio_bridge": True,
    "actual_codex_plugin": True,
    "actual_codex_health_call": True,
    "strict_empty_input": True,
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
    "pnpm-workspace.yaml",
    "crates/local-companion-daemon/Cargo.toml",
    "crates/local-companion-daemon/src/lib.rs",
    "crates/local-companion-daemon/src/main.rs",
    "protocol/private/p17-local-daemon-v1.json",
    "protocol/private/p17-local-mcp-v1.json",
    "web/local-companion-mcp/package.json",
    "web/local-companion-mcp/tsconfig.json",
    "web/local-companion-mcp/src/server.ts",
    "web/local-companion-mcp/src/server.test.ts",
    "tools/p17/run_local_mcp_checks.py",
    "tools/p17/tests/test_local_mcp_checks.py",
    "tools/p17/run_personal_plugin_checks.py",
    "tools/p17/tests/test_personal_plugin_checks.py",
)
GUARD_SOURCES = (
    "tools/p17/local_mcp_plugin_qualification.py",
    "tools/p17/tests/test_local_mcp_plugin_qualification.py",
    "implementation/p17/P17-04_LOCAL_MCP_BRIDGE_V1.md",
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


def expected_bridge_receipt() -> dict[str, Any]:
    return {
        "actual_codex_mcp": True,
        "actual_hangul": False,
        "actual_personal_plugin": False,
        "check_count": len(BRIDGE_CHECKS),
        "checks": list(BRIDGE_CHECKS),
        "decision": "PASS",
        "network_used": False,
        "passed": True,
        "resources_cleaned": True,
        "run_id": BRIDGE_RUN_ID,
        "schema_version": "hwpx-agent.p17-local-mcp-check/v1",
        "scope": "current_pc_local_stdio_mcp_health_only",
        "source_commit": BRIDGE_COMMIT,
        "tracked_clean": True,
    }


def expected_plugin_receipt() -> dict[str, Any]:
    return {
        "actual_codex_plugin": True,
        "actual_hangul": False,
        "check_count": len(PLUGIN_CHECKS),
        "checks": list(PLUGIN_CHECKS),
        "codex_service_used": True,
        "decision": "PASS",
        "ephemeral_codex_thread_id": PLUGIN_THREAD_ID,
        "external_config_hashes": EXTERNAL_HASHES,
        "health_config_sha256": EXTERNAL_HASHES["runtime_sha256"],
        "passed": True,
        "plugin_id": "hwpx-agent-local@personal",
        "plugin_version": "0.1.0",
        "product_network_enabled": False,
        "run_id": PLUGIN_RUN_ID,
        "schema_version": "hwpx-agent.p17-personal-plugin-check/v1",
        "scope": "current_pc_personal_plugin_local_health_only",
        "source_commit": PLUGIN_COMMIT,
        "tracked_clean": True,
    }


def receipt_path(root: Path, kind: str) -> Path:
    if kind == "bridge":
        return root / "artifacts/p17/local-mcp-runs" / BRIDGE_RUN_ID / "receipt.json"
    if kind == "plugin":
        return root / "artifacts/p17/personal-plugin-runs" / PLUGIN_RUN_ID / "receipt.json"
    raise QualificationError("receipt.kind")


def validate_receipt(
    receipt: dict[str, Any], expected: dict[str, Any], code: str
) -> None:
    require(set(receipt) == set(expected), f"{code}.fields")
    require(receipt == expected, f"{code}.claims")


def qualify() -> tuple[Path, Path]:
    bridge_path = receipt_path(ROOT, "bridge")
    plugin_path = receipt_path(ROOT, "plugin")
    bridge = load_document(bridge_path, "bridge_receipt")
    plugin = load_document(plugin_path, "plugin_receipt")
    validate_receipt(bridge, expected_bridge_receipt(), "bridge_receipt")
    validate_receipt(plugin, expected_plugin_receipt(), "plugin_receipt")
    require(digest(bridge_path) == BRIDGE_RECEIPT_SHA256, "bridge_receipt.digest")
    require(digest(plugin_path) == PLUGIN_RECEIPT_SHA256, "plugin_receipt.digest")
    require(plugin_checks.validate_external_configuration() == EXTERNAL_HASHES, "host_state")
    runtime_locks = [source_lock(ROOT, relative) for relative in RUNTIME_SOURCES]
    current = {
        "schema_version": "hwpx-agent.p17-local-mcp-plugin-current/v1",
        "scope": "current_pc_local_mcp_and_personal_plugin_health_only",
        "bridge": {
            "run_id": BRIDGE_RUN_ID,
            "source_commit": BRIDGE_COMMIT,
            "checks": list(BRIDGE_CHECKS),
            "receipt": {
                "path": bridge_path.relative_to(ROOT).as_posix(),
                "sha256": BRIDGE_RECEIPT_SHA256,
            },
        },
        "plugin": {
            "run_id": PLUGIN_RUN_ID,
            "source_commit": PLUGIN_COMMIT,
            "checks": list(PLUGIN_CHECKS),
            "plugin_id": "hwpx-agent-local@personal",
            "ephemeral_codex_thread_id": PLUGIN_THREAD_ID,
            "external_config_hashes": EXTERNAL_HASHES,
            "receipt": {
                "path": plugin_path.relative_to(ROOT).as_posix(),
                "sha256": PLUGIN_RECEIPT_SHA256,
            },
        },
        "claims": CLAIMS,
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
        "schema_version": "hwpx-agent.p17-local-mcp-plugin-qualification/v1",
        "qualification_id": "p17.local-mcp-plugin.v1.20260906",
        "base_commits": {"bridge": BRIDGE_COMMIT, "plugin": PLUGIN_COMMIT},
        "scope": "current_pc_local_mcp_and_personal_plugin_successor_only",
        "claims": CLAIMS,
        "evidence": {
            "path": (
                "implementation/p17/qualification/"
                "local-mcp-plugin-v1-20260906/current-host.json"
            ),
            "canonical_sha256": digest(current_path),
            "bridge_run_id": BRIDGE_RUN_ID,
            "bridge_receipt_sha256": BRIDGE_RECEIPT_SHA256,
            "plugin_run_id": PLUGIN_RUN_ID,
            "plugin_receipt_sha256": PLUGIN_RECEIPT_SHA256,
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
        set(current) == {"bridge", "claims", "plugin", "schema_version", "scope", "source_hashes"}
        and current.get("schema_version") == "hwpx-agent.p17-local-mcp-plugin-current/v1"
        and current.get("scope") == "current_pc_local_mcp_and_personal_plugin_health_only"
        and current.get("claims") == CLAIMS,
        "current.exact",
    )
    bridge = current.get("bridge")
    plugin = current.get("plugin")
    require(
        isinstance(bridge, dict)
        and bridge.get("run_id") == BRIDGE_RUN_ID
        and bridge.get("source_commit") == BRIDGE_COMMIT
        and bridge.get("checks") == list(BRIDGE_CHECKS)
        and bridge.get("receipt")
        == {
            "path": f"artifacts/p17/local-mcp-runs/{BRIDGE_RUN_ID}/receipt.json",
            "sha256": BRIDGE_RECEIPT_SHA256,
        },
        "current.bridge",
    )
    require(
        isinstance(plugin, dict)
        and plugin.get("run_id") == PLUGIN_RUN_ID
        and plugin.get("source_commit") == PLUGIN_COMMIT
        and plugin.get("checks") == list(PLUGIN_CHECKS)
        and plugin.get("plugin_id") == "hwpx-agent-local@personal"
        and plugin.get("ephemeral_codex_thread_id") == PLUGIN_THREAD_ID
        and plugin.get("external_config_hashes") == EXTERNAL_HASHES
        and plugin.get("receipt")
        == {
            "path": f"artifacts/p17/personal-plugin-runs/{PLUGIN_RUN_ID}/receipt.json",
            "sha256": PLUGIN_RECEIPT_SHA256,
        },
        "current.plugin",
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
    require(plugin_checks.validate_external_configuration() == EXTERNAL_HASHES, "host_state")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: local_mcp_plugin_qualification.py RUN_ID|verify|verify-host")
    if sys.argv[1] == PLUGIN_RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_LOCAL_MCP_PLUGIN_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_LOCAL_MCP_PLUGIN_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    elif sys.argv[1] == "verify-host":
        verify_host()
        print("P17_LOCAL_MCP_PLUGIN_HOST_VERIFY_PASS")
    else:
        raise SystemExit("usage: local_mcp_plugin_qualification.py RUN_ID|verify|verify-host")
