from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "protocol/mcp/p15-public-tools-v1.json"
SNAPSHOT_PATH = ROOT / "implementation/p15/p15-public-tool-schema-snapshot-v1.json"
CONTRACT_PATH = ROOT / "implementation/p15/p15-public-tool-schema-contract-v1.json"

SCHEMA_VERSION = "hwpx-agent.mcp-public-tools/v1"
RESULT_VERSION = "hwpx-agent.tool-result/v1"
OFFICIAL_SOURCES = [
    {
        "retrieved_on": "2026-09-04",
        "url": "https://developers.openai.com/plugins/build/mcp-server",
    },
    {
        "retrieved_on": "2026-09-04",
        "url": "https://developers.openai.com/plugins/reference",
    },
    {
        "retrieved_on": "2026-09-04",
        "url": "https://developers.openai.com/plugins/plan/tools",
    },
]

TOOL_ORDER = [
    "capability_check",
    "document_plan",
    "document_create",
    "document_inspect",
    "document_edit",
    "document_transform",
    "template_analyze",
    "document_validate",
    "document_render",
    "document_export",
    "project_create",
    "project_open",
    "project_history",
    "project_checkpoint",
    "project_publish",
    "job_get",
    "job_cancel",
    "artifact_get",
]

AUTH_SCOPES = {
    "capability_check": ["project.read"],
    "document_plan": ["project.read"],
    "document_create": [
        "artifact.read",
        "artifact.write",
        "job.submit",
        "project.read",
        "project.write",
    ],
    "document_inspect": ["artifact.read", "artifact.write", "project.read"],
    "document_edit": [
        "artifact.read",
        "artifact.write",
        "job.submit",
        "project.read",
        "project.write",
    ],
    "document_transform": [
        "artifact.read",
        "artifact.write",
        "job.submit",
        "project.read",
        "project.write",
    ],
    "template_analyze": ["artifact.read", "artifact.write", "project.read"],
    "document_validate": [
        "artifact.read",
        "artifact.write",
        "job.submit",
        "project.read",
    ],
    "document_render": [
        "artifact.read",
        "artifact.write",
        "job.submit",
        "project.read",
    ],
    "document_export": [
        "artifact.read",
        "artifact.write",
        "job.submit",
        "project.read",
    ],
    "project_create": ["project.write"],
    "project_open": ["project.read"],
    "project_history": ["project.read"],
    "project_checkpoint": ["project.read", "project.write"],
    "project_publish": ["project.read", "project.write"],
    "job_get": ["project.read"],
    "job_cancel": ["job.cancel"],
    "artifact_get": ["artifact.read"],
}

# A true readOnlyHint is reserved for tools that cannot create a job, revision,
# artifact, durable snapshot, receipt, or signed delivery grant for any valid input.
READ_ONLY = {
    "capability_check",
    "document_plan",
    "project_open",
    "project_history",
    "job_get",
}

REVISION_MUTATIONS = {
    "document_create",
    "document_edit",
    "document_transform",
    "document_export",
    "project_create",
    "project_checkpoint",
    "project_publish",
    "job_cancel",
}

SOURCE_PATHS = [
    "implementation/p15/P15-02_TOOL_SCHEMA_POLICY.md",
    "implementation/p15/p15-auth-tenant-v1.json",
    "protocol/mcp/p15-public-tools-v1.json",
    "implementation/p15/p15-public-tool-schema-snapshot-v1.json",
    "tools/p01/run_ci.py",
    "tools/p15/build_public_tool_schemas.py",
    "tools/p15/validate_public_tool_schemas.py",
    "tools/p15/tests/test_public_tool_schemas.py",
]


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_value(value: Any) -> str:
    return digest_bytes(canonical_bytes(value))


def string(*, max_length: int = 256, pattern: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"type": "string", "minLength": 1, "maxLength": max_length}
    if pattern is not None:
        result["pattern"] = pattern
    return result


def enum(*values: str) -> dict[str, Any]:
    return {"type": "string", "enum": list(values)}


def integer(minimum: int, maximum: int) -> dict[str, Any]:
    return {"type": "integer", "minimum": minimum, "maximum": maximum}


def number(minimum: float, maximum: float) -> dict[str, Any]:
    return {"type": "number", "minimum": minimum, "maximum": maximum}


def array(items: dict[str, Any], *, min_items: int = 0, max_items: int = 64) -> dict[str, Any]:
    return {
        "type": "array",
        "items": items,
        "minItems": min_items,
        "maxItems": max_items,
    }


def obj(
    properties: dict[str, Any],
    *,
    required: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required or [],
    }


def nullable(schema: dict[str, Any]) -> dict[str, Any]:
    return {"oneOf": [schema, {"type": "null"}]}


def ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/$defs/{name}"}


def definitions() -> dict[str, Any]:
    identifier_tail = r"[A-Za-z0-9_-]{8,120}"
    return {
        "artifact_id": string(max_length=124, pattern=rf"^art_{identifier_tail}$"),
        "capability_id": string(
            max_length=160,
            pattern=r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$",
        ),
        "checkpoint_id": string(max_length=124, pattern=rf"^chk_{identifier_tail}$"),
        "cursor": string(max_length=2048, pattern=r"^[A-Za-z0-9_-]+={0,2}$"),
        "idempotency_key": string(
            max_length=36,
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        ),
        "job_id": string(max_length=124, pattern=rf"^job_{identifier_tail}$"),
        "locale": string(max_length=35, pattern=r"^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-[A-Z]{2}|-[0-9]{3})?$"),
        "media_type": string(
            max_length=127,
            pattern=r"^[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+$",
        ),
        "plan_id": string(max_length=124, pattern=rf"^plan_{identifier_tail}$"),
        "project_id": string(max_length=124, pattern=rf"^prj_{identifier_tail}$"),
        "request_id": string(max_length=124, pattern=rf"^req_{identifier_tail}$"),
        "revision_id": string(max_length=124, pattern=rf"^rev_{identifier_tail}$"),
        "target_profile": {"const": "hancom-hangul-2020-secondary"},
        "template_contract_id": string(max_length=124, pattern=rf"^tpl_{identifier_tail}$"),
        "timestamp": string(
            max_length=40,
            pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?Z$",
        ),
        "warning": obj(
            {
                "code": string(max_length=96, pattern=r"^[A-Z][A-Z0-9_]{2,95}$"),
                "message": string(max_length=1000),
            },
            required=["code", "message"],
        ),
    }


def schema(tool: str, direction: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    all_definitions = definitions()
    used_definitions: set[str] = set()
    pending: list[Any] = [properties]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            reference = value.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/$defs/"):
                name = reference.removeprefix("#/$defs/")
                if name not in all_definitions:
                    raise ValueError(f"unknown local schema definition: {name}")
                if name not in used_definitions:
                    used_definitions.add(name)
                    pending.append(all_definitions[name])
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://schemas.hwpx-agent.local/mcp/{tool}-{direction}-v1.schema.json",
        "title": f"{tool} {direction} v1",
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
        "$defs": {name: all_definitions[name] for name in sorted(used_definitions)},
    }


def context_properties(*, project: bool = True, target: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "client_surface": enum("chatgpt_web", "codex_remote", "codex_local"),
        "locale": ref("locale"),
        "request_id": ref("request_id"),
    }
    if project:
        result["project_id"] = ref("project_id")
    if target:
        result["target_profile"] = ref("target_profile")
    return result


def mutation_properties(*, target: bool = False, new_project: bool = False) -> dict[str, Any]:
    result = context_properties(project=not new_project, target=target)
    result["expected_revision"] = {"type": "null"} if new_project else ref("revision_id")
    result["idempotency_key"] = ref("idempotency_key")
    return result


def input_schema(tool: str) -> dict[str, Any]:
    p: dict[str, Any]
    required: list[str]

    if tool == "capability_check":
        p = context_properties(target=True) | {
            "capabilities": array(ref("capability_id"), min_items=1, max_items=128),
            "revision_id": ref("revision_id"),
            "requirements": obj(
                {
                    "native_editability": {"type": "boolean"},
                    "preserve_unknown": {"type": "boolean"},
                    "required_validation": array(
                        enum(
                            "package",
                            "schema",
                            "semantic",
                            "reopen",
                            "hancom_open",
                            "hancom_save_reopen",
                            "render",
                            "visual_diff",
                            "print_export",
                            "accessibility",
                            "security",
                        ),
                        max_items=11,
                    ),
                },
            ),
        }
        required = ["client_surface", "locale", "request_id", "project_id", "target_profile", "capabilities"]
    elif tool == "document_plan":
        p = context_properties(target=True) | {
            "intent": string(max_length=8000),
            "source_revision_id": nullable(ref("revision_id")),
            "mode": enum("normalized_authoring", "surgical_preserve", "native_automation"),
            "compile_only": {"const": True},
            "constraints": obj(
                {
                    "max_pages": integer(1, 10000),
                    "native_editability": {"type": "boolean"},
                    "preserve_unknown": {"type": "boolean"},
                    "template_contract_id": ref("template_contract_id"),
                }
            ),
        }
        required = ["client_surface", "locale", "request_id", "project_id", "target_profile", "intent", "mode", "compile_only"]
    elif tool == "document_create":
        p = mutation_properties(target=True) | {
            "plan_id": ref("plan_id"),
            "template_artifact_id": ref("artifact_id"),
            "mode": enum("normalized_authoring", "surgical_preserve", "native_automation"),
        }
        required = ["client_surface", "locale", "request_id", "project_id", "target_profile", "expected_revision", "idempotency_key", "plan_id", "mode"]
    elif tool == "document_inspect":
        p = context_properties() | {
            "idempotency_key": ref("idempotency_key"),
            "revision_id": ref("revision_id"),
            "selectors": array(
                enum(
                    "outline", "sections", "range", "node_ids", "styles", "tables",
                    "equations", "drawings", "fields_references", "review_security",
                    "package_parts", "capability_usage",
                ),
                min_items=1,
                max_items=12,
            ),
            "materialization": enum("summary", "properties", "full"),
            "page_size": integer(1, 200),
            "cursor": ref("cursor"),
        }
        required = ["client_surface", "locale", "request_id", "project_id", "idempotency_key", "revision_id", "selectors", "materialization"]
    elif tool == "document_edit":
        p = mutation_properties(target=True) | {
            "source_revision_id": ref("revision_id"),
            "plan_id": ref("plan_id"),
            "dry_run": {"type": "boolean"},
            "best_effort": {"const": False},
            "allow_signature_invalidation": {"type": "boolean"},
        }
        required = ["client_surface", "locale", "request_id", "project_id", "target_profile", "expected_revision", "idempotency_key", "source_revision_id", "plan_id", "dry_run", "best_effort"]
    elif tool == "document_transform":
        p = mutation_properties(target=True) | {
            "source_revision_ids": array(ref("revision_id"), min_items=1, max_items=64),
            "transform": enum(
                "merge", "split", "replace_formatting", "normalize_tables", "normalize_equations",
                "normalize_drawings", "deduplicate_styles", "map_template_styles", "sanitize_metadata",
            ),
            "preview_diff": {"const": True},
            "options": obj(
                {
                    "split_after_pages": array(integer(1, 100000), max_items=1024),
                    "remove_personal_metadata": {"type": "boolean"},
                    "remove_external_links": {"type": "boolean"},
                    "template_contract_id": ref("template_contract_id"),
                }
            ),
        }
        required = ["client_surface", "locale", "request_id", "project_id", "target_profile", "expected_revision", "idempotency_key", "source_revision_ids", "transform", "preview_diff"]
    elif tool == "template_analyze":
        p = context_properties() | {
            "idempotency_key": ref("idempotency_key"),
            "revision_id": ref("revision_id"),
            "materialize_contract": {"type": "boolean"},
            "include_inventory": {"type": "boolean"},
        }
        required = ["client_surface", "locale", "request_id", "project_id", "idempotency_key", "revision_id", "materialize_contract"]
    elif tool == "document_validate":
        p = context_properties(target=True) | {
            "idempotency_key": ref("idempotency_key"),
            "revision_id": ref("revision_id"),
            "levels": array(
                enum(
                    "input", "package", "schema", "relationships", "semantic", "reopen",
                    "hancom_open", "hancom_save_reopen", "render", "visual_diff",
                    "print_export", "accessibility", "security",
                ),
                min_items=1,
                max_items=13,
            ),
            "baseline_revision_id": ref("revision_id"),
            "fail_on_unverified": {"type": "boolean"},
        }
        required = ["client_surface", "locale", "request_id", "project_id", "target_profile", "idempotency_key", "revision_id", "levels", "fail_on_unverified"]
    elif tool == "document_render":
        p = context_properties(target=True) | {
            "idempotency_key": ref("idempotency_key"),
            "revision_id": ref("revision_id"),
            "pages": obj(
                {"first": integer(1, 100000), "last": integer(1, 100000)},
                required=["first", "last"],
            ),
            "dpi": integer(72, 600),
            "output": enum("png", "webp", "pdf"),
            "backend": enum("auto", "hancom_2020", "libreoffice", "internal_preview"),
            "crop": enum("page", "content", "bleed"),
        }
        required = ["client_surface", "locale", "request_id", "project_id", "target_profile", "idempotency_key", "revision_id", "pages", "dpi", "output", "backend"]
    elif tool == "document_export":
        p = mutation_properties(target=True) | {
            "source_revision_id": ref("revision_id"),
            "format": enum("hwp", "hwpx", "pdf", "docx", "rtf", "txt", "html", "daisy", "braille"),
            "profile": enum("editable", "print", "archive", "accessible", "web"),
            "allow_lossy": {"type": "boolean"},
            "include_loss_report": {"const": True},
        }
        required = ["client_surface", "locale", "request_id", "project_id", "target_profile", "expected_revision", "idempotency_key", "source_revision_id", "format", "profile", "allow_lossy", "include_loss_report"]
    elif tool == "project_create":
        p = mutation_properties(target=True, new_project=True) | {
            "display_name": string(max_length=200),
            "default_locale": ref("locale"),
            "retention_class": enum("temporary", "standard", "regulated"),
        }
        required = ["client_surface", "locale", "request_id", "target_profile", "expected_revision", "idempotency_key", "display_name", "default_locale", "retention_class"]
    elif tool == "project_open":
        p = context_properties() | {
            "include": array(
                enum("head", "checkpoints", "warnings", "conflicts", "target", "recent_artifacts", "recommended_actions"),
                min_items=1,
                max_items=7,
            )
        }
        required = ["client_surface", "locale", "request_id", "project_id", "include"]
    elif tool == "project_history":
        p = context_properties() | {
            "from_revision_id": ref("revision_id"),
            "to_revision_id": ref("revision_id"),
            "include_diff_summary": {"type": "boolean"},
            "page_size": integer(1, 200),
            "cursor": ref("cursor"),
        }
        required = ["client_surface", "locale", "request_id", "project_id", "include_diff_summary", "page_size"]
    elif tool == "project_checkpoint":
        p = mutation_properties() | {
            "revision_id": ref("revision_id"),
            "label": string(max_length=120),
            "note": string(max_length=1000),
        }
        required = ["client_surface", "locale", "request_id", "project_id", "expected_revision", "idempotency_key", "revision_id", "label"]
    elif tool == "project_publish":
        p = mutation_properties() | {
            "revision_id": ref("revision_id"),
            "required_gates": array(
                enum("package", "schema", "semantic", "hancom_save_reopen", "render", "visual_diff", "accessibility", "security"),
                min_items=1,
                max_items=8,
            ),
            "release_label": string(max_length=120),
        }
        required = ["client_surface", "locale", "request_id", "project_id", "expected_revision", "idempotency_key", "revision_id", "required_gates", "release_label"]
    elif tool == "job_get":
        p = context_properties() | {
            "job_id": ref("job_id"),
            "include_events": {"type": "boolean"},
            "event_cursor": ref("cursor"),
            "event_limit": integer(1, 200),
        }
        required = ["client_surface", "locale", "request_id", "project_id", "job_id", "include_events"]
    elif tool == "job_cancel":
        p = mutation_properties() | {
            "job_id": ref("job_id"),
            "reason": string(max_length=500),
        }
        required = ["client_surface", "locale", "request_id", "project_id", "expected_revision", "idempotency_key", "job_id", "reason"]
    elif tool == "artifact_get":
        p = context_properties() | {
            "idempotency_key": ref("idempotency_key"),
            "artifact_id": ref("artifact_id"),
            "disposition": enum("metadata", "preview", "attachment"),
            "delivery_ttl_seconds": integer(30, 900),
        }
        required = ["client_surface", "locale", "request_id", "project_id", "idempotency_key", "artifact_id", "disposition"]
    else:
        raise ValueError(f"unknown tool: {tool}")
    return schema(tool, "input", p, required)


def result_base() -> dict[str, Any]:
    return {
        "schema_version": {"const": RESULT_VERSION},
        "request_id": ref("request_id"),
        "outcome": enum("accepted", "succeeded", "partial", "unverified"),
        "safe_summary": string(max_length=1000),
        "warnings": array(ref("warning"), max_items=64),
    }


def artifact_summary() -> dict[str, Any]:
    return obj(
        {
            "artifact_id": ref("artifact_id"),
            "media_type": ref("media_type"),
            "bytes": integer(0, 10_737_418_240),
            "sha256": string(max_length=64, pattern=r"^[0-9a-f]{64}$"),
        },
        required=["artifact_id", "media_type", "bytes", "sha256"],
    )


def output_schema(tool: str) -> dict[str, Any]:
    p = result_base()
    required = ["schema_version", "request_id", "outcome", "safe_summary", "warnings"]

    if tool == "capability_check":
        p["capabilities"] = array(
            obj(
                {
                    "capability_id": ref("capability_id"),
                    "supported": {"type": "boolean"},
                    "support_level": enum("verified", "partial", "unverified", "unsupported"),
                    "selected_backend": enum("direct_hwpx", "hancom_2020", "hybrid", "none"),
                    "estimated_job_class": enum("inline", "short", "long", "unavailable"),
                    "constraints": array(string(max_length=500), max_items=32),
                    "unverified_reasons": array(string(max_length=500), max_items=32),
                },
                required=["capability_id", "supported", "support_level", "selected_backend", "estimated_job_class", "constraints", "unverified_reasons"],
            ),
            min_items=1,
            max_items=128,
        )
        required.append("capabilities")
    elif tool == "document_plan":
        p |= {
            "plan_id": ref("plan_id"),
            "plan_state": enum("valid", "needs_resolution", "invalid"),
            "ambiguities": array(string(max_length=1000), max_items=64),
            "risk_level": enum("low", "medium", "high"),
            "estimated_page_effect": enum("none", "local", "document_wide", "unknown"),
        }
        required += ["plan_id", "plan_state", "ambiguities", "risk_level", "estimated_page_effect"]
    elif tool in {"document_create", "document_edit", "document_transform"}:
        p |= {
            "job_id": nullable(ref("job_id")),
            "revision_id": nullable(ref("revision_id")),
            "artifact": nullable(artifact_summary()),
            "commit_state": enum("not_started", "pending", "committed"),
            "validation_state": enum("not_run", "verified", "partial", "failed"),
        }
        required += ["job_id", "revision_id", "artifact", "commit_state", "validation_state"]
    elif tool == "document_inspect":
        p |= {
            "snapshot_id": string(max_length=124, pattern=r"^snp_[A-Za-z0-9_-]{8,120}$"),
            "items": array(
                obj(
                    {
                        "kind": enum("outline", "section", "range", "node", "style", "table", "equation", "drawing", "reference", "security", "package_part", "capability"),
                        "id": string(max_length=160),
                        "summary": string(max_length=1000),
                    },
                    required=["kind", "id", "summary"],
                ),
                max_items=200,
            ),
            "next_cursor": nullable(ref("cursor")),
            "snapshot_artifact_id": nullable(ref("artifact_id")),
        }
        required += ["snapshot_id", "items", "next_cursor", "snapshot_artifact_id"]
    elif tool == "template_analyze":
        p |= {
            "template_contract_id": ref("template_contract_id"),
            "contract_artifact_id": nullable(ref("artifact_id")),
            "immutable_regions": integer(0, 1_000_000),
            "fillable_slots": integer(0, 1_000_000),
            "unknown_controls": integer(0, 1_000_000),
        }
        required += ["template_contract_id", "contract_artifact_id", "immutable_regions", "fillable_slots", "unknown_controls"]
    elif tool == "document_validate":
        p |= {
            "job_id": ref("job_id"),
            "validation_state": enum("queued", "running", "verified", "partial", "failed", "unverified"),
            "level_results": array(
                obj(
                    {
                        "level": string(max_length=64, pattern=r"^[a-z][a-z0-9_]{1,63}$"),
                        "state": enum("pass", "fail", "unverified", "not_run"),
                        "evidence_artifact_id": nullable(ref("artifact_id")),
                    },
                    required=["level", "state", "evidence_artifact_id"],
                ),
                max_items=13,
            ),
        }
        required += ["job_id", "validation_state", "level_results"]
    elif tool == "document_render":
        p |= {
            "job_id": ref("job_id"),
            "render_state": enum("queued", "running", "succeeded", "partial", "failed", "unverified"),
            "page_count": integer(0, 100000),
            "preview_artifact_id": nullable(ref("artifact_id")),
            "renderer": string(max_length=160),
            "font_substitutions": integer(0, 1_000_000),
        }
        required += ["job_id", "render_state", "page_count", "preview_artifact_id", "renderer", "font_substitutions"]
    elif tool == "document_export":
        p |= {
            "job_id": ref("job_id"),
            "artifact": nullable(artifact_summary()),
            "loss_report_artifact_id": nullable(ref("artifact_id")),
            "export_state": enum("queued", "running", "succeeded", "failed", "unverified"),
        }
        required += ["job_id", "artifact", "loss_report_artifact_id", "export_state"]
    elif tool == "project_create":
        p |= {"project_id": ref("project_id"), "revision_id": nullable(ref("revision_id"))}
        required += ["project_id", "revision_id"]
    elif tool == "project_open":
        p |= {
            "project_id": ref("project_id"),
            "head_revision_id": nullable(ref("revision_id")),
            "warning_count": integer(0, 1_000_000),
            "conflict_state": enum("none", "locked", "stale", "diverged"),
            "recommended_actions": array(string(max_length=500), max_items=32),
        }
        required += ["project_id", "head_revision_id", "warning_count", "conflict_state", "recommended_actions"]
    elif tool == "project_history":
        p |= {
            "revisions": array(
                obj(
                    {
                        "revision_id": ref("revision_id"),
                        "parent_revision_ids": array(ref("revision_id"), max_items=8),
                        "created_at": ref("timestamp"),
                        "summary": string(max_length=500),
                    },
                    required=["revision_id", "parent_revision_ids", "created_at", "summary"],
                ),
                max_items=200,
            ),
            "next_cursor": nullable(ref("cursor")),
        }
        required += ["revisions", "next_cursor"]
    elif tool == "project_checkpoint":
        p |= {"checkpoint_id": ref("checkpoint_id"), "revision_id": ref("revision_id"), "replayed": {"type": "boolean"}}
        required += ["checkpoint_id", "revision_id", "replayed"]
    elif tool == "project_publish":
        p |= {
            "revision_id": ref("revision_id"),
            "publish_state": enum("published", "gate_failed", "unverified"),
            "release_label": string(max_length=120),
            "failed_gates": array(string(max_length=64, pattern=r"^[a-z][a-z0-9_]{1,63}$"), max_items=32),
        }
        required += ["revision_id", "publish_state", "release_label", "failed_gates"]
    elif tool == "job_get":
        p |= {
            "job_id": ref("job_id"),
            "state": enum("queued", "leasing", "running", "validating", "committing", "succeeded", "failed", "cancelled", "expired", "quarantined"),
            "stage": string(max_length=64, pattern=r"^[a-z][a-z0-9_]{1,63}$"),
            "completed_units": integer(0, 1_000_000_000),
            "total_units": nullable(integer(1, 1_000_000_000)),
            "result_artifact_ids": array(ref("artifact_id"), max_items=128),
            "next_event_cursor": nullable(ref("cursor")),
        }
        required += ["job_id", "state", "stage", "completed_units", "total_units", "result_artifact_ids", "next_event_cursor"]
    elif tool == "job_cancel":
        p |= {
            "job_id": ref("job_id"),
            "cancel_state": enum("requested", "cancelled", "already_terminal", "not_cancellable"),
            "receipt_id": string(max_length=124, pattern=r"^rcp_[A-Za-z0-9_-]{8,120}$"),
            "replayed": {"type": "boolean"},
        }
        required += ["job_id", "cancel_state", "receipt_id", "replayed"]
    elif tool == "artifact_get":
        p |= {
            "artifact": artifact_summary(),
            "delivery": enum("metadata", "preview_in_meta", "attachment_in_content"),
            "expires_at": nullable(ref("timestamp")),
        }
        required += ["artifact", "delivery", "expires_at"]
    else:
        raise ValueError(f"unknown tool: {tool}")
    return schema(tool, "output", p, required)


TITLES = {
    "capability_check": "Check document capability",
    "document_plan": "Plan document operation",
    "document_create": "Create document",
    "document_inspect": "Inspect document",
    "document_edit": "Edit document revision",
    "document_transform": "Transform document set",
    "template_analyze": "Analyze document template",
    "document_validate": "Validate document revision",
    "document_render": "Render document preview",
    "document_export": "Export document",
    "project_create": "Create document project",
    "project_open": "Open document project",
    "project_history": "Read project history",
    "project_checkpoint": "Checkpoint project revision",
    "project_publish": "Publish validated revision",
    "job_get": "Get document job",
    "job_cancel": "Cancel document job",
    "artifact_get": "Get artifact",
}

DESCRIPTIONS = {
    "capability_check": "Use before planning when support for requested document capabilities must be checked against the current Hancom 2020 target and caller permissions. This does not run the operation.",
    "document_plan": "Use to compile a bounded natural-language document request into a validated immutable plan. This never changes a project, document, job, or artifact.",
    "document_create": "Use to create a new immutable document revision from a previously validated plan, optionally with a template. This may start a job and never overwrites an existing revision.",
    "document_inspect": "Use to inspect selected document structure, formatting, objects, package parts, or security facts. Full materialization may create a durable bounded snapshot, so it is not annotated read-only.",
    "document_edit": "Use to atomically apply a validated plan to one source revision with an exact revision precondition. The source remains immutable; success creates a new revision.",
    "document_transform": "Use for bounded merge, split, normalization, style mapping, or metadata sanitization across immutable source revisions. Always produces a preview diff and may run asynchronously.",
    "template_analyze": "Use to derive slots, immutable regions, preserve rules, and risky-control inventory from a template revision. Materializing the template contract may create an artifact.",
    "document_validate": "Use to run explicitly selected package, semantic, Hancom 2020, render, accessibility, or security checks. Missing backends remain unverified and validation creates evidence/job state.",
    "document_render": "Use to create bounded page previews or a PDF from a revision with renderer provenance. This creates a job or artifact and does not mutate the source revision.",
    "document_export": "Use to export an immutable revision to one supported document format and generate a semantic-loss report. This only creates local artifacts and never uploads, emails, or prints them.",
    "project_create": "Use to create a tenant-scoped document project with an explicit empty expected revision and replay-safe idempotency key.",
    "project_open": "Use to resume a project by reading its current head, warnings, conflicts, target, recent artifacts, or recommended next actions. This creates no state.",
    "project_history": "Use to page through the immutable revision graph and bounded semantic summaries between revisions. This creates no state.",
    "project_checkpoint": "Use to attach an immutable label to an exact project revision. Retries with the same idempotency key return the same checkpoint.",
    "project_publish": "Use to promote an exact revision to a local delivery label only after every requested validation gate passes. This does not transmit the artifact outside the service.",
    "job_get": "Use to read the current state, progress, result artifacts, and bounded event cursor of one asynchronous job. This creates no state.",
    "job_cancel": "Use to request safe cancellation of one queued or running job. Cancellation is best-effort, receipt-backed, idempotent, and potentially irreversible for that job.",
    "artifact_get": "Use after authorization to request bounded artifact metadata, preview delivery, or attachment delivery. Delivery data stays in MCP content or client-only metadata, not structured output.",
}


def annotations(tool: str) -> dict[str, bool]:
    return {
        "readOnlyHint": tool in READ_ONLY,
        "destructiveHint": tool == "job_cancel",
        "idempotentHint": True,
        "openWorldHint": False,
    }


def descriptor(tool: str) -> dict[str, Any]:
    security = [{"type": "oauth2", "scopes": AUTH_SCOPES[tool]}]
    return {
        "name": tool,
        "title": TITLES[tool],
        "description": DESCRIPTIONS[tool],
        "inputSchema": input_schema(tool),
        "outputSchema": output_schema(tool),
        "securitySchemes": security,
        "annotations": annotations(tool),
        "_meta": {"securitySchemes": deepcopy(security)},
    }


def build_catalog() -> dict[str, Any]:
    tools = [descriptor(name) for name in TOOL_ORDER]
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": "current_pc_hancom_2020_contract_only",
        "official_sources": OFFICIAL_SOURCES,
        "descriptor_count": len(tools),
        "safety_policy": {
            "external_effects_exposed": False,
            "raw_com_or_xml_exposed": False,
            "structured_content_contains_secrets": False,
            "unverified_backend_never_passes": True,
        },
        "tools": tools,
    }


def build_snapshot(catalog: dict[str, Any]) -> dict[str, Any]:
    entries = []
    for tool in catalog["tools"]:
        entries.append(
            {
                "name": tool["name"],
                "annotations": tool["annotations"],
                "security_scopes": tool["securitySchemes"][0]["scopes"],
                "input_schema_sha256": digest_value(tool["inputSchema"]),
                "output_schema_sha256": digest_value(tool["outputSchema"]),
                "descriptor_sha256": digest_value(tool),
            }
        )
    return {
        "schema_version": "hwpx-agent.p15-public-tool-schema-snapshot/v1",
        "catalog_schema_version": SCHEMA_VERSION,
        "catalog_sha256": digest_value(catalog),
        "descriptor_count": len(entries),
        "entries": entries,
    }


def build_contract(root: Path) -> dict[str, Any]:
    locks = []
    for relative in SOURCE_PATHS:
        path = root / relative
        locks.append({"path": relative, "sha256": digest_bytes(path.read_bytes())})
    return {
        "schema_version": "hwpx-agent.p15-public-tool-schema-contract/v1",
        "scope": "current_pc_hancom_2020_contract_only",
        "tool_names": TOOL_ORDER,
        "state_creating_or_mutating_tools": [name for name in TOOL_ORDER if name not in READ_ONLY],
        "revision_mutation_tools": [name for name in TOOL_ORDER if name in REVISION_MUTATIONS],
        "destructive_tools": ["job_cancel"],
        "open_world_tools": [],
        "source_locks": locks,
    }


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def generated_values() -> tuple[dict[str, Any], dict[str, Any]]:
    catalog = build_catalog()
    return catalog, build_snapshot(catalog)


def write_all(root: Path) -> None:
    catalog, snapshot = generated_values()
    write_atomic(CATALOG_PATH, canonical_bytes(catalog))
    write_atomic(SNAPSHOT_PATH, canonical_bytes(snapshot))
    write_atomic(CONTRACT_PATH, canonical_bytes(build_contract(root)))


def check_all(root: Path) -> list[str]:
    catalog, snapshot = generated_values()
    expected = {
        CATALOG_PATH: canonical_bytes(catalog),
        SNAPSHOT_PATH: canonical_bytes(snapshot),
    }
    errors: list[str] = []
    for path, data in expected.items():
        if not path.is_file() or path.read_bytes() != data:
            errors.append(f"generated_drift:{path.relative_to(root).as_posix()}")
    if CONTRACT_PATH.is_file():
        contract = build_contract(root)
        if CONTRACT_PATH.read_bytes() != canonical_bytes(contract):
            errors.append(f"generated_drift:{CONTRACT_PATH.relative_to(root).as_posix()}")
    else:
        errors.append(f"generated_missing:{CONTRACT_PATH.relative_to(root).as_posix()}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write:
        write_all(ROOT)
        print(json.dumps({"state": "written", "tools": len(TOOL_ORDER)}, sort_keys=True))
        return 0
    errors = check_all(ROOT)
    print(json.dumps({"state": "pass" if not errors else "fail", "tools": len(TOOL_ORDER), "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
