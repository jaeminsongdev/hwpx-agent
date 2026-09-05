from __future__ import annotations

import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any, Mapping
import zipfile

import universal_package as universal


ROOT = Path(__file__).resolve().parents[2]
COMPONENT_ROOT = ROOT / "plugins/components/hwpx-agent-skills"
CATALOG_PATH = ROOT / "protocol/mcp/p15-public-tools-v1.json"
ROUTING_CASES_PATH = ROOT / "implementation/p16/p16-skill-routing-cases-v1.json"
ARTIFACT_ROOT = ROOT / "artifacts/p16/packages"
SKILL_NAMES = (
    "build-hancom-tables",
    "compose-math-exam",
    "configure-page-layout",
    "create-hancom-document",
    "edit-hancom-document",
    "insert-native-equations",
    "resume-hancom-project",
    "template-preserve-fill",
    "validate-export-hancom",
)
PUBLIC_TOOL_NAMES = (
    "artifact_get",
    "capability_check",
    "document_create",
    "document_edit",
    "document_export",
    "document_inspect",
    "document_plan",
    "document_render",
    "document_transform",
    "document_validate",
    "job_cancel",
    "job_get",
    "project_checkpoint",
    "project_create",
    "project_history",
    "project_open",
    "project_publish",
    "template_analyze",
)
PUBLIC_CATALOG_SHA256 = "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001"
PRIMARY_TOOL_SEQUENCES = {
    "build-hancom-tables": (
        "project_open", "capability_check", "document_plan", "document_edit", "job_get",
        "document_inspect", "document_validate", "document_render",
    ),
    "compose-math-exam": (
        "project_create", "capability_check", "document_plan", "document_create",
        "job_get", "document_validate", "document_render", "artifact_get",
    ),
    "configure-page-layout": (
        "project_open", "document_inspect", "capability_check", "document_plan",
        "document_edit", "job_get", "document_validate", "document_render",
    ),
    "create-hancom-document": (
        "project_create", "capability_check", "document_plan", "document_create",
        "job_get", "document_validate", "document_render", "artifact_get",
    ),
    "edit-hancom-document": (
        "project_open", "document_inspect", "document_plan", "document_edit",
        "job_get", "document_validate", "document_render",
    ),
    "insert-native-equations": (
        "project_open", "document_inspect", "capability_check", "document_plan",
        "document_edit", "job_get", "document_validate", "document_render",
    ),
    "resume-hancom-project": (
        "project_open", "project_history", "job_get", "project_checkpoint",
    ),
    "template-preserve-fill": (
        "project_open", "template_analyze", "document_plan", "document_edit",
        "job_get", "document_validate", "document_render",
    ),
    "validate-export-hancom": (
        "document_inspect", "document_validate", "job_get", "document_render",
        "document_export", "artifact_get",
    ),
}
OPTIONAL_TOOL_REFERENCES = {"resume-hancom-project": ("job_cancel",)}
SKILL_LIMIT_BYTES = 16 * 1024
COMPONENT_LIMIT_BYTES = 256 * 1024
ARCHIVE_LIMIT_BYTES = 384 * 1024
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TOOL_REFERENCE = re.compile(r"`([a-z][a-z0-9_]+)`")
PRIMARY_TOOL = re.compile(r"(?m)^\d+\.\s+`([a-z][a-z0-9_]+)`:")
FORBIDDEN_TEXT = (
    "HAction.",
    "HWPFrame.",
    "Authorization: Bearer",
    "C:\\",
    "D:\\",
    "[TODO:",
    "YOUR_ORG",
    "example.com",
)
ROUTING_RULES = (
    ("compose-math-exam", ("수학 시험지", "수학 문제지", "math exam", "answer sheet")),
    ("template-preserve-fill", ("양식을 그대로 유지", "기존 양식", "company template", "template while preserving")),
    ("resume-hancom-project", ("프로젝트 작업을 계속", "프로젝트의 체크포인트", "resume the prior", "latest checkpoint")),
    ("validate-export-hancom", ("검증하고 pdf", "pdf로 내보내고 검증", "validate the document", "render a preview")),
    ("insert-native-equations", ("latex 수식", "mathml", "native equation", "편집 가능한 수식")),
    ("build-hancom-tables", ("행 4열 표", "표를 만들", "add a table", "formula cells")),
    ("configure-page-layout", ("여백", "용지를", "가로 방향", "page layout", "landscape", "two columns")),
    ("edit-hancom-document", ("기존 hwpx 문서", "existing document", "문구를 수정")),
    ("create-hancom-document", ("새 hwpx", "새 문서", "새 안내문", "create a new korean document")),
)
UNSUPPORTED_ROUTING_MARKERS = (
    "직접 인쇄",
    "프린터로",
    "printer",
    "haction",
    "raw xml",
    "execute com",
)


def sha256_bytes(value: bytes) -> str:
    return universal.sha256_bytes(value)


def canonical_json_bytes(value: Any) -> bytes:
    return universal.canonical_json_bytes(value)


def expected_entry_names() -> tuple[str, ...]:
    return tuple(f"skills/{name}/SKILL.md" for name in SKILL_NAMES)


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction()) if callable(is_junction) else False


def _has_link_component(path: Path) -> bool:
    current = path.absolute()
    while True:
        if current.exists() and _is_link_like(current):
            return True
        if current.parent == current:
            return False
        current = current.parent


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str, list[str]]:
    if not text.startswith("---\n"):
        return None, "", ["skill.frontmatter.start"]
    end = text.find("\n---\n", 4)
    if end < 0:
        return None, "", ["skill.frontmatter.end"]
    fields: dict[str, str] = {}
    errors: list[str] = []
    for line in text[4:end].splitlines():
        if ":" not in line:
            errors.append("skill.frontmatter.line")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in fields:
            errors.append(f"skill.frontmatter.duplicate:{key}")
        fields[key] = value
    if set(fields) != {"name", "description"}:
        errors.append("skill.frontmatter.fields")
    return fields, text[end + 5 :], sorted(set(errors))


def load_public_catalog() -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    try:
        raw = CATALOG_PATH.read_bytes()
        parsed, json_errors = universal.load_json_bytes(raw, "catalog")
    except OSError:
        return {}, ["catalog.read"]
    errors.extend(json_errors)
    if sha256_bytes(raw) != PUBLIC_CATALOG_SHA256:
        errors.append("catalog.digest")
    if parsed is None or not isinstance(parsed.get("tools"), list):
        return {}, sorted(set(errors + ["catalog.tools"]))
    tools: dict[str, dict[str, Any]] = {}
    for tool in parsed["tools"]:
        if not isinstance(tool, dict) or not isinstance(tool.get("name"), str):
            errors.append("catalog.tool")
            continue
        name = tool["name"]
        if name in tools:
            errors.append(f"catalog.duplicate:{name}")
        tools[name] = tool
    if tuple(sorted(tools)) != PUBLIC_TOOL_NAMES:
        errors.append("catalog.names")
    for name, tool in tools.items():
        required = tool.get("inputSchema", {}).get("required")
        schemes = tool.get("securitySchemes")
        meta_schemes = tool.get("_meta", {}).get("securitySchemes")
        annotations = tool.get("annotations")
        if not isinstance(required, list) or not required or len(required) != len(set(required)):
            errors.append(f"catalog.required:{name}")
        if not isinstance(schemes, list) or schemes != meta_schemes:
            errors.append(f"catalog.security_schemes:{name}")
        if (
            not isinstance(annotations, dict)
            or set(annotations) != {"readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"}
            or any(not isinstance(value, bool) for value in annotations.values())
        ):
            errors.append(f"catalog.annotations:{name}")
    edit_required = tools.get("document_edit", {}).get("inputSchema", {}).get("required", [])
    if "dry_run" not in edit_required or "best_effort" not in edit_required:
        errors.append("catalog.document_edit_required_fields")
    destructive = sorted(name for name, tool in tools.items() if tool.get("annotations", {}).get("destructiveHint") is True)
    if destructive != ["job_cancel"]:
        errors.append("catalog.destructive_boundary")
    return tools, sorted(set(errors))


def validate_skill_bytes(name: str, value: bytes, catalog: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not NAME.fullmatch(name) or name not in SKILL_NAMES:
        errors.append("skill.name")
    if not 1 <= len(value) <= SKILL_LIMIT_BYTES:
        errors.append("skill.bytes")
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError:
        return sorted(set(errors + ["skill.utf8"]))
    if "\x00" in text:
        errors.append("skill.nul")
    if "\r" in text:
        errors.append("skill.line_endings")
    if any(marker.casefold() in text.casefold() for marker in FORBIDDEN_TEXT):
        errors.append("skill.forbidden_text")
    fields, body, frontmatter_errors = parse_frontmatter(text)
    errors.extend(frontmatter_errors)
    if fields is not None:
        if fields.get("name") != name:
            errors.append("skill.frontmatter.name")
        description = fields.get("description", "")
        if not 80 <= len(description) <= 360 or "<" in description or ">" in description:
            errors.append("skill.frontmatter.description")
    if not body.startswith(f"\n# ") or len(body.strip()) < 300:
        errors.append("skill.body")
    referenced = TOOL_REFERENCE.findall(text)
    unknown = sorted(set(referenced) - set(catalog))
    if unknown:
        errors.extend(f"skill.unknown_tool:{tool}" for tool in unknown)
    expected_references = set(PRIMARY_TOOL_SEQUENCES[name]) | set(OPTIONAL_TOOL_REFERENCES.get(name, ()))
    if set(referenced) != expected_references:
        errors.append("skill.tool_references")
    if tuple(PRIMARY_TOOL.findall(text)) != PRIMARY_TOOL_SEQUENCES[name]:
        errors.append("skill.primary_sequence")
    if "document_edit" in referenced and ("dry run true" not in text or "best effort false" not in text):
        errors.append("skill.document_edit_required_fields")
    if name == "resume-hancom-project" and "fresh explicit cancellation request and host confirmation" not in text:
        errors.append("skill.cancel_confirmation")
    if name == "validate-export-hancom" and "No public\ndirect-print tool exists" not in text:
        errors.append("skill.print_boundary")
    return sorted(set(errors))


def read_component_entries(component_root: Path = COMPONENT_ROOT) -> tuple[dict[str, bytes], list[str]]:
    errors: list[str] = []
    entries: dict[str, bytes] = {}
    if not component_root.is_dir() or _has_link_component(component_root):
        return entries, ["component.root"]
    catalog, catalog_errors = load_public_catalog()
    errors.extend(catalog_errors)
    for path in component_root.rglob("*"):
        relative = path.relative_to(component_root).as_posix()
        if _is_link_like(path):
            errors.append(f"component.symlink:{relative}")
        elif path.is_file():
            try:
                entries[relative] = path.read_bytes()
            except OSError:
                errors.append(f"component.read:{relative}")
    if set(entries) != set(expected_entry_names()):
        errors.append("component.entries")
    total = sum(len(value) for value in entries.values())
    if not 1 <= total <= COMPONENT_LIMIT_BYTES:
        errors.append("component.total_bytes")
    for name in SKILL_NAMES:
        entry = f"skills/{name}/SKILL.md"
        value = entries.get(entry)
        if value is None:
            errors.append(f"component.missing:{name}")
        else:
            errors.extend(f"{name}:{error}" for error in validate_skill_bytes(name, value, catalog))
    return entries, sorted(set(errors))


def component_snapshot(entries: Mapping[str, bytes]) -> list[dict[str, Any]]:
    return [
        {"path": name, "bytes": len(entries[name]), "sha256": sha256_bytes(entries[name])}
        for name in sorted(entries)
    ]


def tool_snapshot(tool: Mapping[str, Any]) -> dict[str, Any]:
    schemes = tool.get("securitySchemes", [])
    scopes = sorted({scope for scheme in schemes if isinstance(scheme, dict) for scope in scheme.get("scopes", [])})
    annotations = tool.get("annotations", {})
    return {
        "name": tool["name"],
        "required_input_fields": list(tool.get("inputSchema", {}).get("required", [])),
        "oauth_scopes": scopes,
        "annotations": {
            "readOnlyHint": annotations.get("readOnlyHint"),
            "destructiveHint": annotations.get("destructiveHint"),
            "idempotentHint": annotations.get("idempotentHint"),
            "openWorldHint": annotations.get("openWorldHint"),
        },
    }


def skill_tool_snapshot(name: str, entries: Mapping[str, bytes], catalog: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    text = entries[f"skills/{name}/SKILL.md"].decode("utf-8")
    referenced = sorted(set(TOOL_REFERENCE.findall(text)))
    return {
        "name": name,
        "primary_tool_sequence": list(PRIMARY_TOOL_SEQUENCES[name]),
        "referenced_tools": [tool_snapshot(catalog[tool]) for tool in referenced],
    }


def evaluate_prompt(prompt: str) -> str | None:
    normalized = " ".join(prompt.casefold().split())
    if any(marker in normalized for marker in UNSUPPORTED_ROUTING_MARKERS):
        return None
    for skill, markers in ROUTING_RULES:
        if any(marker in normalized for marker in markers):
            return skill
    return None


def load_routing_cases(path: Path = ROUTING_CASES_PATH) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        parsed, errors = universal.load_json_bytes(path.read_bytes(), "routing")
    except OSError:
        return [], ["routing.read"]
    if errors or parsed is None:
        return [], errors
    if set(parsed) != {"schema_version", "cases"} or parsed.get("schema_version") != "hwpx-agent.p16-skill-routing-cases/v1":
        errors.append("routing.schema")
    cases = parsed.get("cases")
    if not isinstance(cases, list):
        return [], sorted(set(errors + ["routing.cases"]))
    ids: set[str] = set()
    coverage = {name: {"positive": 0, "negative": 0} for name in SKILL_NAMES}
    required = {"id", "kind", "prompt", "skill", "expected_selected_skill"}
    for case in cases:
        if not isinstance(case, dict) or set(case) != required:
            errors.append("routing.case.fields")
            continue
        case_id = case.get("id")
        kind = case.get("kind")
        skill = case.get("skill")
        prompt = case.get("prompt")
        expected = case.get("expected_selected_skill")
        if not isinstance(case_id, str) or not re.fullmatch(r"P16-03-C[0-9]{2}", case_id) or case_id in ids:
            errors.append("routing.case.id")
        else:
            ids.add(case_id)
        if kind not in {"positive", "negative"} or skill not in coverage:
            errors.append("routing.case.classification")
            continue
        coverage[skill][kind] += 1
        if not isinstance(prompt, str) or not 8 <= len(prompt) <= 240:
            errors.append("routing.case.prompt")
            continue
        if expected is not None and expected not in SKILL_NAMES:
            errors.append("routing.case.expected")
        actual = evaluate_prompt(prompt)
        if actual != expected:
            errors.append(f"routing.case.result:{case_id}")
        if kind == "positive" and expected != skill:
            errors.append(f"routing.case.positive:{case_id}")
        if kind == "negative" and expected == skill:
            errors.append(f"routing.case.negative:{case_id}")
    if len(cases) != 36 or any(counts != {"positive": 2, "negative": 2} for counts in coverage.values()):
        errors.append("routing.coverage")
    return cases, sorted(set(errors))


def compose_plugin_entries(base_entries: Mapping[str, bytes], component_entries: Mapping[str, bytes]) -> tuple[dict[str, bytes], list[str]]:
    errors = universal.validate_base_entries(base_entries)
    catalog, catalog_errors = load_public_catalog()
    errors.extend(catalog_errors)
    if set(component_entries) != set(expected_entry_names()):
        errors.append("composition.component_entries")
    for name in SKILL_NAMES:
        entry = f"skills/{name}/SKILL.md"
        if entry in component_entries:
            errors.extend(f"{name}:{error}" for error in validate_skill_bytes(name, component_entries[entry], catalog))
    if errors:
        return {}, sorted(set(errors))
    manifest, parse_errors = universal.load_json_bytes(base_entries[".codex-plugin/plugin.json"], "manifest")
    if parse_errors or manifest is None:
        return {}, parse_errors
    manifest["skills"] = "./skills/"
    composed = dict(base_entries)
    composed[".codex-plugin/plugin.json"] = canonical_json_bytes(manifest)
    composed.update(component_entries)
    return composed, []


def _validate_archive_entries(entries: Mapping[str, bytes], *, composed_plugin: bool) -> list[str]:
    if composed_plugin:
        base_entries, base_errors = universal.read_base_entries()
        component_entries = {name: value for name, value in entries.items() if name.startswith("skills/")}
        expected, compose_errors = compose_plugin_entries(base_entries, component_entries)
        if base_errors or compose_errors or entries != expected:
            return sorted(set(base_errors + compose_errors + ["archive.composed_entries"]))
        return []
    expected_entries, errors = read_component_entries()
    if entries != expected_entries:
        errors.append("archive.component_entries")
    return sorted(set(errors))


def validate_archive(path: Path, *, composed_plugin: bool) -> list[str]:
    errors: list[str] = []
    if _has_link_component(path) or not path.is_file():
        return ["archive.path"]
    try:
        archive_bytes = path.read_bytes()
    except OSError:
        return ["archive.read"]
    if not 1 <= len(archive_bytes) <= ARCHIVE_LIMIT_BYTES:
        errors.append("archive.bytes")
    entries: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                errors.append("archive.duplicate_entry")
            for info in infos:
                candidate = PurePosixPath(info.filename)
                if candidate.is_absolute() or ".." in candidate.parts or info.is_dir():
                    errors.append("archive.entry_path")
                    continue
                if info.compress_type != zipfile.ZIP_STORED:
                    errors.append("archive.compression")
                if info.date_time != (1980, 1, 1, 0, 0, 0):
                    errors.append("archive.timestamp")
                if info.create_system != 3 or (info.external_attr >> 16) != 0o100644:
                    errors.append("archive.permissions")
                if info.flag_bits & 0x1:
                    errors.append("archive.encrypted")
                entries[info.filename] = archive.read(info)
    except (OSError, RuntimeError, zipfile.BadZipFile):
        return sorted(set(errors + ["archive.format"]))
    errors.extend(_validate_archive_entries(entries, composed_plugin=composed_plugin))
    if archive_bytes != universal.deterministic_zip_bytes(entries):
        errors.append("archive.determinism")
    return sorted(set(errors))


def _validate_output_path(output: Path) -> list[str]:
    resolved = output.resolve()
    errors: list[str] = []
    if output.suffix.lower() != ".zip":
        errors.append("output.extension")
    if output.exists():
        errors.append("output.exists")
    if _has_link_component(output.parent):
        errors.append("output.link_component")
    if resolved.is_relative_to(ROOT.resolve()) and not resolved.is_relative_to(ARTIFACT_ROOT.resolve()):
        errors.append("output.tracked_tree")
    return sorted(set(errors))


def publish_archive(output: Path, *, composed_plugin: bool) -> tuple[dict[str, Any] | None, list[str]]:
    component_entries, errors = read_component_entries()
    errors.extend(_validate_output_path(output))
    if composed_plugin:
        base_entries, base_errors = universal.read_base_entries()
        errors.extend(base_errors)
        entries, compose_errors = compose_plugin_entries(base_entries, component_entries)
        errors.extend(compose_errors)
    else:
        entries = component_entries
    if errors:
        return None, sorted(set(errors))
    archive_bytes = universal.deterministic_zip_bytes(entries)
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
    except OSError:
        return None, ["output.publish"]
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(archive_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary_name, output)
    except FileExistsError:
        return None, ["output.exists"]
    except OSError:
        return None, ["output.publish"]
    finally:
        Path(temporary_name).unlink(missing_ok=True)
    return {
        "archive": str(output.resolve()),
        "bytes": len(archive_bytes),
        "entries": len(entries),
        "kind": "composed_plugin" if composed_plugin else "skills_component",
        "sha256": sha256_bytes(archive_bytes),
    }, []
