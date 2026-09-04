from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE_LOCK_PATH = ROOT / "protocol/apps/p16-official-source-lock-v1.json"
CONTRACT_PATH = ROOT / "implementation/p16/p16-official-source-contract-v1.json"

RETRIEVED_AT = "2026-09-04T23:01:49Z"
SCOPE = "current_pc_hangul_2020_local_contract_only"

MUTABLE_DOCUMENTS: list[dict[str, Any]] = [
    {
        "id": "openai.chatgpt-ui",
        "publisher": "OpenAI",
        "url": "https://developers.openai.com/plugins/build/chatgpt-ui",
        "snapshot_url": "https://developers.openai.com/plugins/build/chatgpt-ui.md",
        "retrieved_at": RETRIEVED_AT,
        "content_length_bytes": 26036,
        "sha256": "2dcc3b5a9927a879670394cb755ea1e667f59baba344702f35fd655e66a690d9",
        "topics": ["mcp_apps_first", "decoupled_render_tools", "resource_metadata", "csp"],
    },
    {
        "id": "openai.plugin-package",
        "publisher": "OpenAI",
        "url": "https://developers.openai.com/plugins/build/plugins",
        "snapshot_url": "https://developers.openai.com/plugins/build/plugins.md",
        "retrieved_at": RETRIEVED_AT,
        "content_length_bytes": 22899,
        "sha256": "605face331e44ea6befdc54c63b3d1e560f0595635db9083a20b9bbd19554e18",
        "topics": ["plugin_manifest", "registered_app_mapping", "path_rules", "local_marketplace"],
    },
    {
        "id": "openai.connect-test",
        "publisher": "OpenAI",
        "url": "https://developers.openai.com/plugins/deploy/connect-chatgpt",
        "snapshot_url": "https://developers.openai.com/plugins/deploy/connect-chatgpt.md",
        "retrieved_at": RETRIEVED_AT,
        "content_length_bytes": 6554,
        "sha256": "11694ac732e312c06b92c8a29bc9cd4796bcbe075f890b5a3b50fe284fdca4ca",
        "topics": ["developer_mode", "inspector", "positive_negative_eval", "metadata_refresh"],
    },
    {
        "id": "openai.plugin-reference",
        "publisher": "OpenAI",
        "url": "https://developers.openai.com/plugins/reference",
        "snapshot_url": "https://developers.openai.com/plugins/reference.md",
        "retrieved_at": RETRIEVED_AT,
        "content_length_bytes": 31711,
        "sha256": "3fb11cddbe6b48ee360217085c0debd08a72b9bd7cb52e982a045bd3f6df0704",
        "topics": ["window_openai_extensions", "result_visibility", "legacy_compatibility", "file_flow"],
    },
    {
        "id": "openai.ui-guidelines",
        "publisher": "OpenAI",
        "url": "https://developers.openai.com/plugins/concepts/ui-guidelines",
        "snapshot_url": "https://developers.openai.com/plugins/concepts/ui-guidelines.md",
        "retrieved_at": RETRIEVED_AT,
        "content_length_bytes": 12256,
        "sha256": "30ef2884a431c31ac9aaff92a714dc561434132c064f69a31fa04ee357600481",
        "topics": ["inline_first", "action_limits", "responsive_layout", "accessibility"],
    },
    {
        "id": "openai.security-privacy",
        "publisher": "OpenAI",
        "url": "https://developers.openai.com/plugins/guides/security-privacy",
        "snapshot_url": "https://developers.openai.com/plugins/guides/security-privacy.md",
        "retrieved_at": RETRIEVED_AT,
        "content_length_bytes": 3387,
        "sha256": "9d8e03b4e59413b8de01da3f5bc1d2f5bc7bdc6c4add398b538c6a85d559391b",
        "topics": ["least_privilege", "confirmation", "server_validation", "redaction"],
    },
    {
        "id": "openai.examples-index",
        "publisher": "OpenAI",
        "url": "https://developers.openai.com/plugins/build/examples",
        "snapshot_url": "https://developers.openai.com/plugins/build/examples.md",
        "retrieved_at": RETRIEVED_AT,
        "content_length_bytes": 617,
        "sha256": "b77507dfcfec72650e72faf2b04db4369fe13916c735bea479bc71c5f5dc7035",
        "topics": ["official_examples", "end_to_end_reference"],
    },
    {
        "id": "mcp.apps-overview",
        "publisher": "Model Context Protocol",
        "url": "https://modelcontextprotocol.io/extensions/apps/overview",
        "snapshot_url": "https://modelcontextprotocol.io/extensions/apps/overview.md",
        "retrieved_at": RETRIEVED_AT,
        "content_length_bytes": 12907,
        "sha256": "ebae6e6d71c0561230261caf3b84a7493bd55beae704593accc6e1bceedb0e39",
        "topics": ["progressive_enhancement", "sandbox", "postmessage", "capability_negotiation"],
    },
    {
        "id": "mcp.apps-build",
        "publisher": "Model Context Protocol",
        "url": "https://modelcontextprotocol.io/extensions/apps/build",
        "snapshot_url": "https://modelcontextprotocol.io/extensions/apps/build.md",
        "retrieved_at": RETRIEVED_AT,
        "content_length_bytes": 20587,
        "sha256": "3b722db818cea428f123ff21e396847a4ddec2b31e83a90a86413ebb64727957",
        "topics": ["register_app_tool", "register_app_resource", "single_file_bundle", "deny_by_default_csp"],
    },
]

IMMUTABLE_SOURCES: list[dict[str, Any]] = [
    {
        "id": "openai.apps-sdk-examples",
        "kind": "git_commit",
        "url": "https://github.com/openai/openai-apps-sdk-examples",
        "ref": "refs/heads/main",
        "commit": "18cc38e78a968712c357bacdc3c79fead5bfc6b4",
        "retrieved_at": RETRIEVED_AT,
    },
    {
        "id": "mcp.ext-apps-release",
        "kind": "git_tag",
        "url": "https://github.com/modelcontextprotocol/ext-apps",
        "ref": "refs/tags/v1.7.5",
        "commit": "92f46a574568a3ddac7600343b7d3c4c4ed7b588",
        "retrieved_at": RETRIEVED_AT,
    },
    {
        "id": "mcp.apps-spec-2026-01-26",
        "kind": "content_at_commit",
        "url": "https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/92f46a574568a3ddac7600343b7d3c4c4ed7b588/specification/2026-01-26/apps.mdx",
        "commit": "92f46a574568a3ddac7600343b7d3c4c4ed7b588",
        "content_length_bytes": 59181,
        "sha256": "ee452a7d1b9b7fb900acfeb4d6932d3963375b0f3f37d196a4b93eb80312af0e",
        "status": "stable_2026-01-26",
        "retrieved_at": RETRIEVED_AT,
    },
]

PACKAGE_LOCKS: list[dict[str, Any]] = [
    {
        "id": "mcp.ext-apps-package",
        "name": "@modelcontextprotocol/ext-apps",
        "version": "1.7.5",
        "integrity": "sha512-TjPH2S2y5UEGKhmI6+XGFuqfqOV4ppe1x6DA3txnUaEWkgtA4G5vo14jGKFZmegdkZ1H4QMLyujLvoU1BEdnAg==",
        "tarball": "https://registry.npmjs.org/@modelcontextprotocol/ext-apps/-/ext-apps-1.7.5.tgz",
        "adoption": "required_for_p16_04_after_explicit_dependency_review",
    },
    {
        "id": "openai.apps-sdk-ui-package",
        "name": "@openai/apps-sdk-ui",
        "version": "0.2.2",
        "integrity": "sha512-KaG+6qcVCKVRe51wr2te68OKoHfjRQPDVVkugxiF+SaZlgLpNbxOfyrL/FyUBmHbjh1q4p7eWDYAd75jHseZ9A==",
        "tarball": "https://registry.npmjs.org/@openai/apps-sdk-ui/-/apps-sdk-ui-0.2.2.tgz",
        "adoption": "optional_for_p16_04_after_bundle_and_accessibility_review",
    },
]


def requirement(
    requirement_id: str,
    category: str,
    normative: str,
    target: str,
    sources: list[str],
    statement: str,
) -> dict[str, Any]:
    return {
        "id": requirement_id,
        "category": category,
        "normative": normative,
        "implementation_target": target,
        "sources": sources,
        "statement": statement,
    }


REQUIREMENTS: list[dict[str, Any]] = [
    requirement("P16-R01", "architecture", "MUST", "P16-04", ["openai.chatgpt-ui", "mcp.apps-overview"], "Use MCP Apps as the portable UI foundation."),
    requirement("P16-R02", "architecture", "MUST", "P16-04", ["openai.chatgpt-ui", "mcp.apps-overview"], "Keep every underlying MCP workflow useful when the host does not render UI."),
    requirement("P16-R03", "architecture", "MUST", "P16-04", ["openai.chatgpt-ui"], "Keep P15 data and action tools UI-independent; only dedicated versioned render tools may declare a UI resource."),
    requirement("P16-R04", "ui_resource", "MUST", "P16-04", ["openai.chatgpt-ui", "mcp.apps-build"], "Use a versioned ui:// resource URI and change it for breaking HTML, JavaScript, or CSS revisions."),
    requirement("P16-R05", "ui_resource", "MUST", "P16-04", ["openai.chatgpt-ui", "mcp.apps-build", "mcp.apps-spec-2026-01-26"], "Serve UI resources as text/html;profile=mcp-app, preferably through RESOURCE_MIME_TYPE."),
    requirement("P16-R06", "bridge", "MUST", "P16-04", ["openai.chatgpt-ui", "mcp.apps-overview", "mcp.apps-spec-2026-01-26"], "Use the MCP Apps ui/* JSON-RPC lifecycle over postMessage for initialization, notifications, tool calls, messages, and context."),
    requirement("P16-R07", "bridge", "MUST", "P16-04", ["openai.chatgpt-ui", "openai.plugin-reference"], "Use window.openai only for feature-detected ChatGPT extensions that have no shared MCP Apps equivalent; never branch on a host name."),
    requirement("P16-R08", "bridge", "MUST", "P16-04", ["openai.plugin-reference"], "Treat absent approval-gated tool input before ui/notifications/tool-input as an expected lifecycle state."),
    requirement("P16-R09", "result_data", "MUST", "P16-04", ["openai.plugin-reference"], "Keep structuredContent concise, output-schema-valid, and safe for both the model and component."),
    requirement("P16-R10", "result_data", "MUST", "P16-04", ["openai.plugin-reference", "openai.security-privacy"], "Place component-only hydration data in result _meta, exclude secrets, and re-authorize every server call instead of trusting hidden client data."),
    requirement("P16-R11", "manifest", "MUST", "P16-02", ["openai.plugin-package"], "Provide the required plugin entry point at .codex-plugin/plugin.json."),
    requirement("P16-R12", "manifest", "MUST", "P16-02", ["openai.plugin-package"], "Keep manifest paths ./-relative, resolve them from the plugin root, and reject root escape."),
    requirement("P16-R13", "manifest", "MUST", "P16-02", ["openai.plugin-package"], "Use the compatibility apps field only for .app.json registered MCP mappings; accept the plugin_asdk_app identifier only from an actual developer-mode registration."),
    requirement("P16-R14", "manifest", "MUST", "P16-02", ["openai.plugin-package"], "Use mcpServers/.mcp.json only for a bundled server and do not confuse it with a registered remote MCP mapping."),
    requirement("P16-R15", "manifest", "MUST", "P16-03", ["openai.plugin-package", "openai.connect-test"], "Package nine workflow skills and verify each skill against the actual versioned public tool names with positive and negative evaluations."),
    requirement("P16-R16", "csp", "MUST", "P16-09", ["openai.chatgpt-ui", "openai.security-privacy", "mcp.apps-build"], "Declare exact HTTPS origins only, with no wildcard, for every network or resource dependency."),
    requirement("P16-R17", "csp", "MUST", "P16-04", ["openai.chatgpt-ui", "mcp.apps-overview"], "Place standard CSP in each returned resource content item at _meta.ui.csp."),
    requirement("P16-R18", "csp", "MUST", "P16-09", ["openai.chatgpt-ui", "openai.security-privacy"], "Keep nested frames disabled by omitting frameDomains unless a reviewed exact origin is indispensable."),
    requirement("P16-R19", "csp", "MUST", "P16-08", ["openai.plugin-reference"], "Prefer _meta.ui.csp; use legacy openai/widgetCSP only when compatibility is required, including redirect_domains for approved openExternal destinations."),
    requirement("P16-R20", "csp", "MUST", "P16-09", ["openai.plugin-reference"], "Treat a unique hosted _meta.ui.domain as submission evidence and leave it unverified until hosting and submission scope exist."),
    requirement("P16-R21", "file_flow", "MUST", "P16-08", ["openai.chatgpt-ui", "openai.plugin-reference"], "Feature-detect ChatGPT uploadFile, selectFiles, and getFileDownloadUrl and provide a non-ChatGPT fallback or an explicit unavailable state."),
    requirement("P16-R22", "file_flow", "MUST", "P16-08", ["openai.plugin-reference", "openai.security-privacy"], "Expose only bounded opaque file, artifact, project, revision, and job identifiers plus summaries to the model; never place document bytes in model-visible output."),
    requirement("P16-R23", "file_flow", "MUST", "P16-08", ["openai.security-privacy"], "Validate upload ownership, tenant, ACL, media type, size, and digest server-side and reject local filesystem paths."),
    requirement("P16-R24", "file_flow", "MUST", "P16-08", ["openai.plugin-reference", "openai.connect-test"], "Deliver outputs through artifact_get or a host file reference with bounded expiry and a fresh authorization and ACL check."),
    requirement("P16-R25", "design", "SHOULD", "P16-04", ["openai.chatgpt-ui", "openai.ui-guidelines"], "Start inline and request the smallest display mode that can complete the task."),
    requirement("P16-R26", "design", "MUST", "P16-05", ["openai.ui-guidelines"], "Limit inline cards to one primary and at most one secondary action, with no deep navigation or nested scrolling."),
    requirement("P16-R27", "accessibility", "MUST", "P16-09", ["openai.ui-guidelines"], "Verify keyboard operation, visible focus, semantic labels, readable contrast, responsive sizing, host theme, locale, and reduced-motion behavior."),
    requirement("P16-R28", "security", "MUST", "P16-06", ["openai.security-privacy"], "Use least privilege, explicit consent, and host confirmation for write or irreversible actions."),
    requirement("P16-R29", "security", "MUST", "P16-06", ["openai.security-privacy"], "Validate every model- or UI-originated input server-side and treat prompt injection and malicious files as expected inputs."),
    requirement("P16-R30", "security", "MUST", "P16-09", ["openai.security-privacy"], "Redact PII and secrets from logs, retain bounded correlation identifiers, and avoid raw prompt or document logging."),
    requirement("P16-R31", "validation", "MUST", "P16-09", ["openai.connect-test"], "Use MCP Inspector to verify tool discovery and representative, edge, missing-identifier, empty-result, authentication, annotation, confirmation, and model-readable-result behavior."),
    requirement("P16-R32", "validation", "MUST", "P16-09", ["openai.connect-test"], "In an explicit user-operated developer-mode session, test positive, indirect, follow-up, write-confirmation, unsupported, and boundary prompts plus UI console and state restoration."),
    requirement("P16-R33", "claim_boundary", "MUST", "P16-01", ["openai.plugin-package", "openai.connect-test"], "Do not claim local installation, developer-mode connectivity, public hosting, workspace publication, universal publication, or submission from this source-review card."),
    requirement("P16-R34", "claim_boundary", "MUST", "P16-02", ["openai.security-privacy"], "Never accept or emit raw HWPX XML, HAction or COM identifiers, arbitrary local paths, credentials, or unbounded document content through public or model-visible contracts."),
]

DEFERRED_EVIDENCE = [
    {
        "id": "registered_openai_app_id",
        "state": "unverified",
        "reason": "Requires an actual developer-mode MCP registration; no identifier is invented or stored in P16-01.",
        "earliest_task": "P16-02",
    },
    {
        "id": "chatgpt_developer_mode_connection",
        "state": "unverified",
        "reason": "Requires user-operated ChatGPT account and workspace UI plus a reachable endpoint or secure tunnel.",
        "earliest_task": "P16-09",
    },
    {
        "id": "public_https_and_unique_widget_domain",
        "state": "unverified",
        "reason": "Production hosting and submission are outside the current-PC local scope.",
        "earliest_task": "P19",
    },
    {
        "id": "chatgpt_file_library_roundtrip",
        "state": "unverified",
        "reason": "The host extension and account capability must be feature-detected in an explicit user session.",
        "earliest_task": "P16-08",
    },
    {
        "id": "real_hangul_execution_from_web",
        "state": "unverified",
        "reason": "P16-01 is contract-only and does not launch Hangul or invoke COM.",
        "earliest_task": "P16-09",
    },
    {
        "id": "hangul_2022_2024_or_other_pc",
        "state": "unverified",
        "reason": "Only the current PC licensed Hangul 2020 target is in scope; later versions wait for their own PCs.",
        "earliest_task": "later_cross_version_session",
    },
]

LOCAL_SOURCE_PATHS = [
    "implementation/p16/P16-01_OFFICIAL_SOURCE_POLICY.md",
    "protocol/apps/p16-official-source-lock-v1.json",
    "tools/p16/build_official_source_contract.py",
    "tools/p16/run_checks.py",
    "tools/p16/validate_official_source_contract.py",
    "tools/p16/tests/test_official_source_contract.py",
]


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def build_source_lock() -> dict[str, Any]:
    categories = sorted({entry["category"] for entry in REQUIREMENTS})
    return {
        "schema_version": "hwpx-agent.p16-official-source-lock/v1",
        "task": "P16-01",
        "retrieved_at": RETRIEVED_AT,
        "scope": SCOPE,
        "source_precedence": [
            "stable_mcp_apps_specification",
            "current_openai_plugin_documentation",
            "pinned_official_examples_and_package_releases",
            "local_product_contracts",
        ],
        "portable_bridge": "mcp_apps",
        "chatgpt_extension_policy": "feature_detect_window_openai_only_when_no_shared_mcp_apps_equivalent",
        "csp_policy": {
            "metadata_location": "resource_contents._meta.ui.csp",
            "connect_domains": [],
            "resource_domains": [],
            "frame_domains": [],
            "redirect_domains": [],
            "wildcard_allowed": False,
            "origin_scheme": "https",
        },
        "mutable_documents": MUTABLE_DOCUMENTS,
        "immutable_sources": IMMUTABLE_SOURCES,
        "package_locks": PACKAGE_LOCKS,
        "requirements": REQUIREMENTS,
        "review_summary": {
            "document_count": len(MUTABLE_DOCUMENTS),
            "immutable_source_count": len(IMMUTABLE_SOURCES),
            "package_count": len(PACKAGE_LOCKS),
            "requirement_count": len(REQUIREMENTS),
            "categories": categories,
            "manifest_reviewed": True,
            "ui_reviewed": True,
            "csp_reviewed": True,
            "file_flow_reviewed": True,
            "developer_mode_reviewed": True,
        },
        "deferred_evidence": DEFERRED_EVIDENCE,
        "next_task": "P16-02 Universal package",
    }


def build_contract(source_lock: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    source_locks = [
        {
            "path": relative,
            "sha256": sha256_file(root / relative),
        }
        for relative in LOCAL_SOURCE_PATHS
    ]
    return {
        "schema_version": "hwpx-agent.p16-official-source-contract/v1",
        "task": "P16-01",
        "scope": SCOPE,
        "source_lock": {
            "path": SOURCE_LOCK_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256_bytes(canonical_bytes(source_lock)),
        },
        "review": source_lock["review_summary"],
        "source_locks": source_locks,
        "decision": "pass_scoped_current_pc_hangul_2020_source_contract_only",
        "claims": {
            "official_sources_locked": True,
            "manifest_requirements_reviewed": True,
            "ui_requirements_reviewed": True,
            "plugin_bundle_implemented": False,
            "widget_implemented": False,
            "developer_mode_tested": False,
            "public_or_production_ready": False,
            "hangul_or_com_invoked": False,
        },
        "next_task": source_lock["next_task"],
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the P16-01 official source lock and contract.")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()

    source_lock = build_source_lock()
    source_bytes = canonical_bytes(source_lock)
    if args.write:
        atomic_write(SOURCE_LOCK_PATH, source_bytes)
        contract = build_contract(source_lock)
        atomic_write(CONTRACT_PATH, canonical_bytes(contract))
        print(
            json.dumps(
                {
                    "decision": "PASS",
                    "source_lock": SOURCE_LOCK_PATH.relative_to(ROOT).as_posix(),
                    "contract": CONTRACT_PATH.relative_to(ROOT).as_posix(),
                    "documents": len(MUTABLE_DOCUMENTS),
                    "requirements": len(REQUIREMENTS),
                    "local_source_locks": len(LOCAL_SOURCE_PATHS),
                },
                sort_keys=True,
            )
        )
        return 0

    errors: list[str] = []
    if not SOURCE_LOCK_PATH.is_file() or SOURCE_LOCK_PATH.read_bytes() != source_bytes:
        errors.append("source_lock")
    if not errors:
        expected_contract = canonical_bytes(build_contract(source_lock))
        if not CONTRACT_PATH.is_file() or CONTRACT_PATH.read_bytes() != expected_contract:
            errors.append("contract")
    if errors:
        print(json.dumps({"decision": "FAIL", "errors": errors}, sort_keys=True))
        return 1
    print(json.dumps({"decision": "PASS", "documents": len(MUTABLE_DOCUMENTS), "requirements": len(REQUIREMENTS)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
