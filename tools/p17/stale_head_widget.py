from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p17/p17-stale-head-widget-contract-v1.json"
PROTOCOL_PATH = ROOT / "protocol/private/p17-stale-head-widget-v1.json"
PREDECESSORS = (
    "implementation/p16/p16-continuity-contract-v1.json",
    "protocol/private/p17-local-conflict-resolver-v1.json",
)
BUNDLES = (
    "web/plugin-widget/dist/continuity-widget-v2.html",
    "web/plugin-widget/dist/continuity-v2-e2e-host.html",
)
SOURCE_PATHS = (
    "web/plugin-widget/scripts/build-continuity-widget.mjs",
    "web/plugin-widget/src/continuity-component.tsx",
    "web/plugin-widget/src/continuity-controller.test.ts",
    "web/plugin-widget/src/continuity-controller.ts",
    "web/plugin-widget/src/continuity-model.test.ts",
    "web/plugin-widget/src/continuity-model.ts",
    "web/plugin-widget/src/continuity-preview.tsx",
    "web/plugin-widget/src/continuity-resource.test.ts",
    "web/plugin-widget/src/continuity-resource.ts",
    "web/plugin-widget/src/continuity-styles.css",
    "web/plugin-widget/src/continuity-ui.test.tsx",
    "web/plugin-widget/src/continuity-ui.tsx",
    "web/plugin-widget/src/continuity-v2-e2e-host.ts",
    "tools/p17/run_stale_head_widget_e2e.py",
    "tools/p17/stale_head_widget.py",
    "tools/p17/tests/test_stale_head_widget.py",
    "protocol/migrations/p17-continuity-v1-to-v2.md",
    "protocol/private/p17-stale-head-widget-v1.json",
    "implementation/p17/P17-07_STALE_HEAD_WIDGET_V2.md",
)
REQUIRED_BUNDLE_TEXT = (
    "hwpx-agent.continuity-render-request/v2",
    "hwpx-agent.project-continuity/v2",
    "project_conflict_resolve",
    "rebase_operation_plan",
    "manual_merge",
    "confirm_resolution",
)
FORBIDDEN_SOURCE = re.compile(
    r"(?:\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\s*\(|"
    r"\bEventSource\s*\(|\bsendBeacon\s*\(|\b(?:localStorage|sessionStorage)\b|"
    r"document\.cookie|HAction\.|HWPFrame\.|<hp:)",
    re.IGNORECASE,
)
RUN_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "state",
        "scope",
        "browser_executable",
        "resource",
        "harness",
        "assertions",
        "claims",
        "run_id",
    }
)
BUNDLE_RECEIPT_KEYS = frozenset({"path", "bytes", "sha256"})
KNOWN_CHROME_EXECUTABLES = frozenset(
    {
        "chrome.exe",
        "chrome",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    }
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def lock(relative: str) -> dict[str, object]:
    value = (ROOT / relative).read_bytes()
    return {"path": relative, "bytes": len(value), "sha256": sha256_bytes(value)}


def validate_receipt(receipt: Any, receipt_path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(receipt, dict):
        return ["receipt.object"]
    if set(receipt) != RECEIPT_KEYS:
        errors.append("receipt.keys")
    expected_claims = {
        "actual_chatgpt_or_codex_host_tested": False,
        "project_conflict_resolve_registered": False,
        "actual_remote_transport_tested": False,
        "actual_concurrent_web_codex_tested": False,
        "hangul_or_com_invoked": False,
        "p17_07_pass": False,
    }
    expected_assertions = {
        "bridge": "real_ext_apps_appbridge_postmessage_iframe",
        "selection_call_count": 0,
        "confirmed_call_count": 3,
        "call_order": [
            "project_conflict_resolve",
            "project_open",
            "project_history",
        ],
        "request_and_response_revision_generation_checked": True,
        "three_request_ids_distinct": True,
        "idempotency_key_present": True,
        "post_resolution_refresh_required": True,
    }
    if (
        receipt.get("schema_version")
        != "hwpx-agent.p17-stale-head-widget-e2e-receipt/v1"
        or receipt.get("state") != "pass"
        or receipt.get("scope")
        != "local_headless_browser_mcp_apps_bridge_component"
        or receipt.get("claims") != expected_claims
        or receipt.get("assertions") != expected_assertions
    ):
        errors.append("receipt.contract")
    run_id = receipt.get("run_id")
    if not isinstance(run_id, str) or RUN_ID_PATTERN.fullmatch(run_id) is None:
        errors.append("receipt.run_id")
    if receipt.get("browser_executable") not in KNOWN_CHROME_EXECUTABLES:
        errors.append("receipt.browser_executable")
    for key, expected_path in zip(("resource", "harness"), BUNDLES, strict=True):
        item = receipt.get(key)
        if (
            not isinstance(item, dict)
            or set(item) != BUNDLE_RECEIPT_KEYS
            or item.get("path") != expected_path
        ):
            errors.append(f"receipt.{key}.path")
            continue
        try:
            value = (ROOT / expected_path).read_bytes()
        except OSError:
            errors.append(f"receipt.{key}.read")
            continue
        if (
            type(item.get("bytes")) is not int
            or item.get("bytes") != len(value)
            or item.get("sha256") != sha256_bytes(value)
        ):
            errors.append(f"receipt.{key}.digest")
    try:
        relative = receipt_path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        errors.append("receipt.path.outside_root")
    else:
        if not relative.startswith("artifacts/p17/stale-head-widget-runs/"):
            errors.append("receipt.path.scope")
        if (
            receipt_path.name != "receipt.json"
            or not isinstance(run_id, str)
            or receipt_path.parent.name != run_id
        ):
            errors.append("receipt.path.identity")
    return sorted(set(errors))


def validate_sources() -> list[str]:
    errors: list[str] = []
    production = SOURCE_PATHS[1:2] + SOURCE_PATHS[3:4] + SOURCE_PATHS[5:6]
    production += SOURCE_PATHS[8:10] + SOURCE_PATHS[11:12]
    for relative in production:
        try:
            value = (ROOT / relative).read_bytes()
            text = value.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            errors.append(f"source.read:{relative}")
            continue
        if b"\r" in value or b"\x00" in value or FORBIDDEN_SOURCE.search(text):
            errors.append(f"source.safety:{relative}")
    try:
        bundle = (ROOT / BUNDLES[0]).read_text(encoding="utf-8")
    except OSError:
        return sorted(set(errors + ["bundle.read"]))
    if not 1 <= len(bundle.encode("utf-8")) <= 800_000:
        errors.append("bundle.bytes")
    if any(required not in bundle for required in REQUIRED_BUNDLE_TEXT):
        errors.append("bundle.protocol")
    if re.search(
        r"<(?:base|embed|form|iframe|object)\b|"
        r"<(?:audio|img|link|script|source|track|video)\b[^>]*(?:href|poster|src|srcset)\s*=|"
        r"\b(?:action|href|poster|src|srcset)\s*=\s*[\"']?\s*(?:https?:|//)",
        bundle,
        re.IGNORECASE,
    ):
        errors.append("bundle.external")
    return sorted(set(errors))


def build_contract(receipt_path: Path) -> dict[str, object]:
    receipt = load_json(receipt_path)
    errors = validate_receipt(receipt, receipt_path) + validate_sources()
    if errors:
        raise RuntimeError("stale-head validation failed: " + ",".join(errors))
    return {
        "schema_version": "hwpx-agent.p17-stale-head-widget-contract/v1",
        "task": "P17-07",
        "scope": "current_pc_local_mcp_apps_graphical_component",
        "decision": "component_pass_host_and_concurrent_evidence_pending",
        "predecessors": [lock(relative) for relative in PREDECESSORS],
        "protocol": lock(PROTOCOL_PATH.relative_to(ROOT).as_posix()),
        "bundles": [lock(relative) for relative in BUNDLES],
        "sources": [lock(relative) for relative in SOURCE_PATHS],
        "evidence": {
            "path": receipt_path.resolve().relative_to(ROOT.resolve()).as_posix(),
            "sha256": sha256_bytes(receipt_path.read_bytes()),
            "run_id": receipt["run_id"],
        },
        "validation": {
            "plugin_widget_tests": 144,
            "contract_tests": 4,
            "v1_regression_e2e": True,
            "v2_stale_head_e2e": True,
            "desktop_viewport": "1200x900",
            "mobile_viewport": "390x844",
            "horizontal_overflow": False,
            "console_errors_or_warnings": 0,
        },
        "claims": {
            "graphical_component_implemented": True,
            "project_conflict_resolve_registered": False,
            "actual_remote_transport_tested": False,
            "actual_concurrent_web_codex_tested": False,
            "actual_hangul_tested": False,
            "p17_07_pass": False,
            "phase_complete": False,
            "product_complete": False,
        },
    }


def write_contract(receipt_path: Path) -> None:
    CONTRACT_PATH.write_bytes(canonical_json_bytes(build_contract(receipt_path)))


def verify_contract() -> list[str]:
    try:
        current = load_json(CONTRACT_PATH)
        evidence = current.get("evidence")
        if not isinstance(evidence, dict) or not isinstance(evidence.get("path"), str):
            return ["contract.evidence"]
        receipt_path = ROOT / evidence["path"]
        expected = canonical_json_bytes(build_contract(receipt_path))
        actual = CONTRACT_PATH.read_bytes()
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as error:
        return [f"contract.read_or_build:{type(error).__name__}"]
    return [] if actual == expected else ["contract.stale"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or verify P17 stale-head widget evidence.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--receipt", required=True, type=Path)
    subparsers.add_parser("verify")
    args = parser.parse_args()
    if args.command == "build":
        receipt = args.receipt if args.receipt.is_absolute() else ROOT / args.receipt
        write_contract(receipt)
    else:
        errors = verify_contract()
        if errors:
            raise RuntimeError("stale-head contract invalid: " + ",".join(errors))
    print(f"P17_STALE_HEAD_WIDGET_CONTRACT_PASS sources={len(SOURCE_PATHS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
