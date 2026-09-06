"""Freeze and verify the installed v0.4 widget-plugin prepare qualification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import run_widget_plugin_prepare_checks as host_checks


ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION = ROOT / "implementation/p17/qualification/widget-plugin-prepare-v1-20260906"
RUN_ID = "9e2a6c6e958642e6a7f72dc9dac0bf25"
BASE_COMMIT = "48061260f36619077fb8114ecb8eb86c18edbca5"
RECEIPT_SHA256 = "027c7d38af0c0a510715162002133f88cb5b7cef9a0cffb8bcb5327b38e56e0c"
HEALTH_THREAD_ID = "01a074f0-73c7-7f03-a6e9-f00971affe73"
PREPARE_THREAD_ID = "01a074f0-c4ef-7fc2-a094-6ce03e5f5a05"
EXTERNAL_HASHES = {
    "daemon_sha256": "9fbae0e05ed40fd8e6b5431435490cb0a07307f6084b05308438d569d59151b8",
    "git_sha256": "81ef35ae005ca9318018d18e3327578ce939fb99feaad6b2d7c8ab15f3de8db5",
    "manifest_sha256": "4f4ddc6069f1cdc900d86035aa76449daa2e5685661ecaf13b00d3753a5888fd",
    "mcp_sha256": "3d549bfd7b75faf68ea22c4bc136a941de8d94ee7115528863758b1ac5073ab8",
    "node_sha256": "b3094d0b49f9ad602262a9921551737bb97637c05dd357a06ae98188d7290aa3",
    "runtime_sha256": "b1a294a5a250f4209db63a76ac98b7d44a1abda345121373cca422eb4577c6e2",
    "server_sha256": "37883655e1ad945f9946e8df3b3239f4152b7b6e6e08912e443c007e43289098",
    "widget_sha256": "8f2543745178871afddba8a532f2caf1c7826d78307930eb4a22b814ff98d608",
}
WORKSPACE_SNAPSHOT = {
    "head": host_checks.EXPECTED_HEAD,
    "index_sha256": "6577c61cce9270669f123900f944ce3a11923628afda9d5bf9159ca20261075b",
    "output_sha256": host_checks.EXPECTED_OUTPUT_SHA256,
    "status_sha256": "0a6e914f14068e709ec51314292b9b67cc209bd5fc82fccba9599d1c0edf485c",
}
PLAN_BINDING = {
    "expected_head": host_checks.EXPECTED_HEAD,
    "expected_head_reference": "refs/heads/main",
    "plan_sha256": "7d6bb5e5d27be3077851e65e132f6042cf122b308ef09ee210a28a81debbdf76",
    "target_sha256": "3f53bb64fbe8d7c28116083b73720ad923a0b73810a2cbcdc728415a5de9da01",
}
CLAIMS = {
    "actual_codex_plugin": True,
    "actual_health_call": True,
    "actual_read_only_prepare": True,
    "actual_trusted_ui": False,
    "actual_git_effect": False,
    "actual_hangul": False,
    "approval_secret_persisted": False,
    "fixture_git_unchanged": True,
    "source_clean_at_run": True,
    "product_network_enabled": False,
    "codex_service_used": True,
    "phase_complete": False,
}
RUNTIME_SOURCES = (
    "Cargo.toml",
    "Cargo.lock",
    "crates/local-companion-daemon/src/lib.rs",
    "crates/local-companion-daemon/src/main.rs",
    "protocol/private/p17-local-daemon-v4.json",
    "protocol/private/p17-local-mcp-v4.json",
    "web/local-companion-mcp/package.json",
    "web/local-companion-mcp/src/server.ts",
    "web/local-companion-mcp/src/server.test.ts",
    "web/plugin-widget/package.json",
    "web/plugin-widget/src/git-approval-component.tsx",
    "web/plugin-widget/src/git-approval-controller.ts",
    "web/plugin-widget/src/git-approval-controller.test.ts",
    "web/plugin-widget/src/git-approval-mcp-app-port.ts",
    "tools/p17/run_personal_plugin_checks.py",
    "tools/p17/run_widget_plugin_prepare_checks.py",
    "tools/p17/tests/test_widget_plugin_prepare_checks.py",
)
GUARD_SOURCES = (
    "tools/p17/widget_plugin_prepare_qualification.py",
    "tools/p17/tests/test_widget_plugin_prepare_qualification.py",
    "implementation/p17/P17-08_TRUSTED_WIDGET_V7.md",
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
        "actual_git_effect": False,
        "actual_hangul": False,
        "actual_health_call": True,
        "actual_read_only_prepare": True,
        "actual_trusted_ui": False,
        "check_count": len(host_checks.CHECKS),
        "checks": list(host_checks.CHECKS),
        "codex_service_used": True,
        "decision": "PASS",
        "external_hashes": EXTERNAL_HASHES,
        "health_config_sha256": EXTERNAL_HASHES["runtime_sha256"],
        "health_thread_id": HEALTH_THREAD_ID,
        "passed": True,
        "plan_binding": PLAN_BINDING,
        "plugin_id": "hwpx-agent-local@personal",
        "plugin_version": host_checks.PLUGIN_VERSION,
        "prepare_thread_id": PREPARE_THREAD_ID,
        "product_network_enabled": False,
        "run_id": RUN_ID,
        "schema_version": "hwpx-agent.p17-widget-plugin-prepare-check/v1",
        "scope": "current_pc_installed_v04_health_and_read_only_prepare_only",
        "source_commit": BASE_COMMIT,
        "tracked_clean": True,
        "workspace_snapshot": WORKSPACE_SNAPSHOT,
    }


def validate_receipt(receipt: dict[str, Any]) -> None:
    expected = expected_receipt()
    require(set(receipt) == set(expected), "receipt.fields")
    require(receipt == expected, "receipt.claims")


def receipt_path(root: Path) -> Path:
    return root / "artifacts/p17/widget-plugin-prepare-runs" / RUN_ID / "receipt.json"


def expected_current(root: Path) -> dict[str, Any]:
    locks = [source_lock(root, relative) for relative in RUNTIME_SOURCES]
    return {
        "schema_version": "hwpx-agent.p17-widget-plugin-prepare-current/v1",
        "scope": "current_pc_installed_v04_health_and_read_only_prepare_only",
        "run_id": RUN_ID,
        "source_commit": BASE_COMMIT,
        "plugin_id": "hwpx-agent-local@personal",
        "plugin_version": host_checks.PLUGIN_VERSION,
        "health_thread_id": HEALTH_THREAD_ID,
        "prepare_thread_id": PREPARE_THREAD_ID,
        "checks": list(host_checks.CHECKS),
        "external_hashes": EXTERNAL_HASHES,
        "workspace_snapshot": WORKSPACE_SNAPSHOT,
        "plan_binding": PLAN_BINDING,
        "claims": CLAIMS,
        "receipt": {
            "path": f"artifacts/p17/widget-plugin-prepare-runs/{RUN_ID}/receipt.json",
            "sha256": RECEIPT_SHA256,
        },
        "source_hashes": {entry["path"]: entry["sha256"] for entry in locks},
    }


def expected_contract(root: Path, current_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-widget-plugin-prepare-qualification/v1",
        "qualification_id": "p17.widget-plugin-prepare.v1.20260906",
        "base_commit": BASE_COMMIT,
        "scope": "current_pc_installed_v04_read_only_prepare_successor_only",
        "claims": CLAIMS,
        "evidence": {
            "path": (
                "implementation/p17/qualification/"
                "widget-plugin-prepare-v1-20260906/current-host.json"
            ),
            "canonical_sha256": digest(current_path),
            "run_id": RUN_ID,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "runtime_sources": [source_lock(root, relative) for relative in RUNTIME_SOURCES],
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
    }


def qualify() -> tuple[Path, Path]:
    path = receipt_path(ROOT)
    receipt = load_document(path, "receipt")
    validate_receipt(receipt)
    require(digest(path) == RECEIPT_SHA256, "receipt.digest")
    require(host_checks.validate_widget_binding() == EXTERNAL_HASHES, "host_state")
    require(host_checks.path_entries(host_checks.APPROVAL_STATE) == (), "host.secret_state")
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(canonical(expected_current(ROOT)))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


def verify(root: Path = ROOT) -> dict[str, Any]:
    directory = root / QUALIFICATION.relative_to(ROOT)
    current_path = directory / "current-host.json"
    current = load_document(current_path, "current")
    contract = load_document(directory / "contract.json", "contract")
    require(current == expected_current(root), "current.exact")
    require(contract == expected_contract(root, current_path), "contract.exact")
    return contract


def verify_host() -> None:
    verify()
    require(host_checks.validate_widget_binding() == EXTERNAL_HASHES, "host_state")
    require(host_checks.path_entries(host_checks.APPROVAL_STATE) == (), "host.secret_state")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: widget_plugin_prepare_qualification.py RUN_ID|verify|verify-host")
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_WIDGET_PLUGIN_PREPARE_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_WIDGET_PLUGIN_PREPARE_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    elif sys.argv[1] == "verify-host":
        verify_host()
        print("P17_WIDGET_PLUGIN_PREPARE_HOST_VERIFY_PASS")
    else:
        raise SystemExit("usage: widget_plugin_prepare_qualification.py RUN_ID|verify|verify-host")
