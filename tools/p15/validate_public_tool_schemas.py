from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterator

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_public_tool_schemas as builder  # noqa: E402


CATALOG_PATH = builder.CATALOG_PATH
SNAPSHOT_PATH = builder.SNAPSHOT_PATH
CONTRACT_PATH = builder.CONTRACT_PATH
AUTH_CONTRACT_PATH = ROOT / "implementation/p15/p15-auth-tenant-v1.json"

EXPECTED_CATALOG_KEYS = {
    "schema_version",
    "scope",
    "official_sources",
    "descriptor_count",
    "safety_policy",
    "tools",
}
EXPECTED_DESCRIPTOR_KEYS = {
    "name",
    "title",
    "description",
    "inputSchema",
    "outputSchema",
    "securitySchemes",
    "annotations",
    "_meta",
}
EXPECTED_ANNOTATION_KEYS = {
    "readOnlyHint",
    "destructiveHint",
    "idempotentHint",
    "openWorldHint",
}
EXPECTED_CONTRACT_KEYS = {
    "schema_version",
    "scope",
    "tool_names",
    "state_creating_or_mutating_tools",
    "revision_mutation_tools",
    "destructive_tools",
    "open_world_tools",
    "source_locks",
}
FORBIDDEN_SCHEMA_PROPERTIES = {
    "access_token",
    "client_secret",
    "com_action",
    "content_bytes",
    "file_path",
    "haction",
    "local_path",
    "parameter_set",
    "password",
    "raw_xml",
    "secret",
    "signed_url",
}

REF_SAMPLES: dict[str, Any] = {
    "artifact_id": "art_example01",
    "capability_id": "page.paper_preset",
    "checkpoint_id": "chk_example01",
    "cursor": "Y3Vyc29y",
    "idempotency_key": "123e4567-e89b-12d3-a456-426614174000",
    "job_id": "job_example01",
    "locale": "ko-KR",
    "media_type": "application/hwp+zip",
    "plan_id": "plan_example01",
    "project_id": "prj_example01",
    "request_id": "req_example01",
    "revision_id": "rev_example01",
    "target_profile": "hancom-hangul-2020-secondary",
    "template_contract_id": "tpl_example01",
    "timestamp": "2026-09-04T00:00:00Z",
}


def load_json(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key in {path.name}: {key}")
            value[key] = item
        return value

    result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    if not isinstance(result, dict):
        raise ValueError(f"JSON root must be an object: {path.name}")
    return result


def walk(value: Any, path: str = "$") -> Iterator[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from walk(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk(item, f"{path}[{index}]")


def bounded_source_file(root: Path, relative: str, maximum_bytes: int) -> Path:
    value = Path(relative)
    if not relative or "\\" in relative or value.is_absolute() or ".." in value.parts:
        raise ValueError(f"unbounded source path: {relative}")
    candidate = root / value
    if candidate.is_symlink() or (
        hasattr(candidate, "is_junction") and candidate.is_junction()
    ):
        raise ValueError(f"linked source path: {relative}")
    resolved_root = root.resolve(strict=True)
    resolved = candidate.resolve(strict=True)
    if resolved_root not in resolved.parents or not resolved.is_file():
        raise ValueError(f"source is outside repository: {relative}")
    if not 0 < resolved.stat().st_size <= maximum_bytes:
        raise ValueError(f"source size is outside bound: {relative}")
    return resolved


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthesize(node: dict[str, Any], root: dict[str, Any]) -> Any:
    if "$ref" in node:
        reference = node["$ref"]
        name = reference.removeprefix("#/$defs/")
        if reference != f"#/$defs/{name}" or name not in REF_SAMPLES:
            raise ValueError(f"unsupported fixture reference: {reference}")
        return REF_SAMPLES[name]
    if "const" in node:
        return node["const"]
    if "enum" in node:
        return node["enum"][0]
    if "oneOf" in node:
        return synthesize(node["oneOf"][0], root)
    kind = node.get("type")
    if kind == "object":
        properties = node.get("properties", {})
        return {
            key: synthesize(properties[key], root)
            for key in node.get("required", [])
        }
    if kind == "array":
        count = max(0, node.get("minItems", 0))
        return [synthesize(node["items"], root) for _ in range(count)]
    if kind == "boolean":
        return False
    if kind == "integer":
        return node.get("minimum", 0)
    if kind == "number":
        return node.get("minimum", 0)
    if kind == "null":
        return None
    if kind == "string":
        pattern = node.get("pattern", "")
        if pattern == r"^[0-9a-f]{64}$":
            return "a" * 64
        if pattern.startswith("^snp_"):
            return "snp_example01"
        if pattern.startswith("^rcp_"):
            return "rcp_example01"
        if pattern.startswith("^[A-Z]"):
            return "TEST_CODE"
        if pattern.startswith("^[a-z][a-z0-9_]"):
            return "stage"
        if pattern.startswith("^[a-z][a-z0-9_]*(?:\\."):
            return "page.paper"
        return "value"
    raise ValueError(f"unsupported fixture schema node: {node}")


def validate_schema_shape(tool: str, direction: str, schema: Any) -> list[str]:
    errors: list[str] = []
    label = f"{tool}.{direction}"
    if not isinstance(schema, dict):
        return [f"{label}.not_object"]
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as error:  # jsonschema exposes heterogeneous schema errors.
        errors.append(f"{label}.invalid_schema:{type(error).__name__}")
        return errors
    expected_id = f"https://schemas.hwpx-agent.local/mcp/{tool}-{direction}-v1.schema.json"
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append(f"{label}.draft")
    if schema.get("$id") != expected_id:
        errors.append(f"{label}.id")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        errors.append(f"{label}.root_closed")
    properties = schema.get("properties")
    required = schema.get("required")
    if not isinstance(properties, dict) or not isinstance(required, list):
        errors.append(f"{label}.root_shape")
        return errors
    if len(required) != len(set(required)) or not set(required).issubset(properties):
        errors.append(f"{label}.required")
    for path, node in walk(schema):
        if not isinstance(node, dict):
            continue
        if node.get("type") == "object" and node.get("additionalProperties") is not False:
            errors.append(f"{label}.open_object:{path}")
        if node.get("type") == "array" and not isinstance(node.get("maxItems"), int):
            errors.append(f"{label}.unbounded_array:{path}")
        if node.get("type") == "string" and not any(
            key in node for key in ("maxLength", "enum", "const")
        ):
            errors.append(f"{label}.unbounded_string:{path}")
        if node.get("type") in {"integer", "number"} and "maximum" not in node:
            errors.append(f"{label}.unbounded_number:{path}")
        reference = node.get("$ref")
        if isinstance(reference, str) and not reference.startswith("#/$defs/"):
            errors.append(f"{label}.external_ref:{path}")
        nested_properties = node.get("properties")
        if isinstance(nested_properties, dict):
            forbidden = set(nested_properties) & FORBIDDEN_SCHEMA_PROPERTIES
            if forbidden:
                errors.append(f"{label}.forbidden_properties:{path}:{sorted(forbidden)}")
    try:
        sample = synthesize(schema, schema)
    except ValueError as error:
        errors.append(f"{label}.fixture:{error}")
        return errors
    sample_errors = sorted(
        Draft202012Validator(schema).iter_errors(sample), key=lambda item: list(item.path)
    )
    if sample_errors:
        errors.append(f"{label}.fixture_invalid:{sample_errors[0].message}")
    invalid = dict(sample)
    invalid["unexpected_property"] = True
    if Draft202012Validator(schema).is_valid(invalid):
        errors.append(f"{label}.unknown_property_accepted")
    return errors


def validate_source_locks(contract: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    locks = contract.get("source_locks")
    if not isinstance(locks, list) or len(locks) != len(builder.SOURCE_PATHS):
        return ["contract.source_locks"]
    observed: list[str] = []
    for index, lock in enumerate(locks):
        if not isinstance(lock, dict) or set(lock) != {"path", "sha256"}:
            errors.append(f"contract.source_locks[{index}].shape")
            continue
        relative = lock.get("path")
        digest = lock.get("sha256")
        if not isinstance(relative, str) or relative != builder.SOURCE_PATHS[index]:
            errors.append(f"contract.source_locks[{index}].path")
            continue
        observed.append(relative)
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            errors.append(f"contract.source_locks[{index}].digest")
            continue
        try:
            path = bounded_source_file(root, relative, 4 * 1024 * 1024)
        except (OSError, ValueError):
            errors.append(f"contract.source_locks[{index}].missing")
            continue
        if sha256_file(path) != digest:
            errors.append(f"contract.source_locks[{index}].drift")
    if observed != builder.SOURCE_PATHS:
        errors.append("contract.source_locks.order")
    return errors


def validate_contract(contract: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    if set(contract) != EXPECTED_CONTRACT_KEYS:
        errors.append("contract.top_level_keys")
    if contract.get("schema_version") != "hwpx-agent.p15-public-tool-schema-contract/v1":
        errors.append("contract.schema_version")
    if contract.get("scope") != "current_pc_hancom_2020_contract_only":
        errors.append("contract.scope")
    if contract.get("tool_names") != builder.TOOL_ORDER:
        errors.append("contract.tool_names")
    if contract.get("state_creating_or_mutating_tools") != [
        name for name in builder.TOOL_ORDER if name not in builder.READ_ONLY
    ]:
        errors.append("contract.state_creating_or_mutating_tools")
    if contract.get("revision_mutation_tools") != [
        name for name in builder.TOOL_ORDER if name in builder.REVISION_MUTATIONS
    ]:
        errors.append("contract.revision_mutation_tools")
    if contract.get("destructive_tools") != ["job_cancel"]:
        errors.append("contract.destructive_tools")
    if contract.get("open_world_tools") != []:
        errors.append("contract.open_world_tools")
    errors.extend(validate_source_locks(contract, root))
    return errors


def validate_catalog(catalog: dict[str, Any], auth_contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(catalog) != EXPECTED_CATALOG_KEYS:
        errors.append("catalog.top_level_keys")
    if catalog.get("schema_version") != builder.SCHEMA_VERSION:
        errors.append("catalog.schema_version")
    if catalog.get("scope") != "current_pc_hancom_2020_contract_only":
        errors.append("catalog.scope")
    if catalog.get("official_sources") != builder.OFFICIAL_SOURCES:
        errors.append("catalog.official_sources")
    if catalog.get("descriptor_count") != 18:
        errors.append("catalog.descriptor_count")
    if catalog.get("safety_policy") != {
        "external_effects_exposed": False,
        "raw_com_or_xml_exposed": False,
        "structured_content_contains_secrets": False,
        "unverified_backend_never_passes": True,
    }:
        errors.append("catalog.safety_policy")
    tools = catalog.get("tools")
    if not isinstance(tools, list):
        return errors + ["catalog.tools"]
    if [tool.get("name") if isinstance(tool, dict) else None for tool in tools] != builder.TOOL_ORDER:
        errors.append("catalog.tool_order")
    auth_scopes = auth_contract.get("scopes")
    if not isinstance(auth_scopes, list):
        errors.append("auth_contract.scopes")
        auth_scope_set: set[str] = set()
    else:
        auth_scope_set = set(auth_scopes)
    descriptions: set[str] = set()
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            errors.append(f"tool[{index}].shape")
            continue
        name = tool.get("name")
        if not isinstance(name, str) or name not in builder.TOOL_ORDER:
            errors.append(f"tool[{index}].name")
            continue
        if set(tool) != EXPECTED_DESCRIPTOR_KEYS:
            errors.append(f"{name}.descriptor_keys")
        title = tool.get("title")
        description = tool.get("description")
        if not isinstance(title, str) or not 4 <= len(title) <= 80:
            errors.append(f"{name}.title")
        if not isinstance(description, str) or not 40 <= len(description) <= 500:
            errors.append(f"{name}.description")
        elif description in descriptions:
            errors.append(f"{name}.description_duplicate")
        else:
            descriptions.add(description)
        security = tool.get("securitySchemes")
        expected_security = [{"type": "oauth2", "scopes": builder.AUTH_SCOPES[name]}]
        if security != expected_security:
            errors.append(f"{name}.security")
        declared_scopes: list[Any] = []
        if (
            isinstance(security, list)
            and len(security) == 1
            and isinstance(security[0], dict)
            and isinstance(security[0].get("scopes"), list)
        ):
            declared_scopes = security[0]["scopes"]
        if not all(isinstance(scope, str) and scope in auth_scope_set for scope in declared_scopes):
            errors.append(f"{name}.unknown_auth_scope")
        meta = tool.get("_meta")
        if meta != {"securitySchemes": expected_security}:
            errors.append(f"{name}.security_mirror")
        expected_annotations = builder.annotations(name)
        annotations = tool.get("annotations")
        if annotations != expected_annotations or (
            isinstance(annotations, dict) and set(annotations) != EXPECTED_ANNOTATION_KEYS
        ):
            errors.append(f"{name}.annotations")
        errors.extend(validate_schema_shape(name, "input", tool.get("inputSchema")))
        errors.extend(validate_schema_shape(name, "output", tool.get("outputSchema")))
        input_value = tool.get("inputSchema")
        if isinstance(input_value, dict):
            required = input_value.get("required", [])
            if name not in builder.READ_ONLY and "idempotency_key" not in required:
                errors.append(f"{name}.missing_idempotency_key")
            if name in builder.REVISION_MUTATIONS and "expected_revision" not in required:
                errors.append(f"{name}.missing_expected_revision")
            if name == "project_create":
                properties = input_value.get("properties", {})
                if properties.get("expected_revision") != {"type": "null"}:
                    errors.append("project_create.expected_revision_not_null")
                if "target_profile" not in required:
                    errors.append("project_create.missing_target_profile")
            if name in builder.READ_ONLY and (
                "idempotency_key" in input_value.get("properties", {})
                or "expected_revision" in input_value.get("properties", {})
            ):
                errors.append(f"{name}.read_only_state_field")
        output_value = tool.get("outputSchema")
        if isinstance(output_value, dict):
            output_properties = set(output_value.get("properties", {}))
            if not {"schema_version", "request_id", "outcome", "safe_summary", "warnings"}.issubset(output_properties):
                errors.append(f"{name}.output_envelope")
    return errors


def validate_snapshot(snapshot: dict[str, Any], catalog: dict[str, Any]) -> list[str]:
    expected = builder.build_snapshot(catalog)
    if snapshot != expected:
        return ["snapshot.drift"]
    entries = snapshot.get("entries", [])
    if [entry.get("name") for entry in entries] != builder.TOOL_ORDER:
        return ["snapshot.order"]
    return []


def validate_all(
    catalog: dict[str, Any],
    snapshot: dict[str, Any],
    contract: dict[str, Any],
    auth_contract: dict[str, Any],
    root: Path,
) -> list[str]:
    errors = []
    errors.extend(builder.check_all(root))
    errors.extend(validate_contract(contract, root))
    errors.extend(validate_catalog(catalog, auth_contract))
    errors.extend(validate_snapshot(snapshot, catalog))
    return sorted(set(errors))


def main() -> int:
    catalog = load_json(CATALOG_PATH)
    snapshot = load_json(SNAPSHOT_PATH)
    contract = load_json(CONTRACT_PATH)
    auth_contract = load_json(AUTH_CONTRACT_PATH)
    errors = validate_all(catalog, snapshot, contract, auth_contract, ROOT)
    result = {
        "schema_version": "hwpx-agent.p15-public-tool-schema-validation/v1",
        "state": "pass" if not errors else "fail",
        "descriptors": catalog.get("descriptor_count"),
        "input_schemas": len(catalog.get("tools", [])),
        "output_schemas": len(catalog.get("tools", [])),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
