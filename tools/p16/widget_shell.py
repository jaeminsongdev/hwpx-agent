from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "implementation/p16/p16-widget-shell-policy-v1.json"
PACKAGE_PATH = ROOT / "web/plugin-widget/package.json"
LOCK_PATH = ROOT / "pnpm-lock.yaml"
CATALOG_PATH = ROOT / "protocol/mcp/p15-public-tools-v1.json"
BUNDLE_PATH = ROOT / "web/plugin-widget/dist/widget-v1.html"
PREVIEW_PATH = ROOT / "web/plugin-widget/dist/preview.html"
PREDECESSOR_PATH = ROOT / "implementation/p16/p16-skills-package-contract-v1.json"
EXPECTED_PREDECESSOR_SHA256 = "900d1ef22af22e3c701f49d9a8b3e8cd912ebbf559a9b31222051e7c3e6bf8e9"
EXPECTED_CATALOG_SHA256 = "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001"
EXPECTED_REQUIREMENTS = (
    "P16-R01", "P16-R02", "P16-R03", "P16-R04", "P16-R05", "P16-R06",
    "P16-R07", "P16-R08", "P16-R09", "P16-R10", "P16-R17", "P16-R25",
)
EXPECTED_DEPENDENCIES = {
    "@modelcontextprotocol/ext-apps": ("1.7.5", "runtime"),
    "react": ("19.2.8", "runtime"),
    "react-dom": ("19.2.8", "runtime"),
    "esbuild": ("0.28.2", "development"),
}
PUBLIC_TOOL_NAMES = (
    "artifact_get", "capability_check", "document_create", "document_edit",
    "document_export", "document_inspect", "document_plan", "document_render",
    "document_transform", "document_validate", "job_cancel", "job_get",
    "project_checkpoint", "project_create", "project_history", "project_open",
    "project_publish", "template_analyze",
)
FORBIDDEN_BUNDLE_PATTERNS = (
    re.compile(r"new\s+Function\b"),
    re.compile(r"(?<![A-Za-z])eval\s*\("),
    re.compile(r"<(?:base|embed|form|iframe|object)\b", re.IGNORECASE),
    re.compile(r"<meta\b[^>]*http-equiv\s*=\s*[\"']?refresh", re.IGNORECASE),
    re.compile(
        r"<(?:audio|img|link|script|source|track|video)\b[^>]*"
        r"(?:href|poster|src|srcset)\s*=",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:action|href|poster|src|srcset)\s*=\s*[\"']?\s*(?:https?:|//)",
        re.IGNORECASE,
    ),
    re.compile(r"@import\s|url\(\s*[\"']?(?:https?:|//)", re.IGNORECASE),
    re.compile(r"(?:localStorage|sessionStorage|document\.cookie)"),
    re.compile(r"(?:[A-Z]:\\|Authorization:\s*Bearer|HAction\.|HWPFrame\.)"),
)
AUTHORED_BROWSER_SOURCES = (
    "web/plugin-widget/src/bridge.ts",
    "web/plugin-widget/src/component.tsx",
    "web/plugin-widget/src/host-extensions.ts",
    "web/plugin-widget/src/mcp-app-port.ts",
    "web/plugin-widget/src/model.ts",
    "web/plugin-widget/src/ui.tsx",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_json(path: Path) -> tuple[Any | None, list[str]]:
    try:
        raw = path.read_bytes()
    except OSError:
        return None, ["json.read"]
    try:
        text = raw.decode("utf-8")
        return json.loads(text, object_pairs_hook=_reject_duplicate_pairs), []
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None, ["json.parse"]


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def png_dimensions(value: bytes) -> tuple[int, int] | None:
    if len(value) < 24 or value[:8] != b"\x89PNG\r\n\x1a\n" or value[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", value[16:24])


def _contains_resource_uri(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            key in {"resourceUri", "ui/resourceUri", "openai/outputTemplate"}
            or _contains_resource_uri(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_resource_uri(item) for item in value)
    return False


def validate_policy(policy: Any, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    required_keys = {
        "schema_version", "task", "bundle", "csp", "dependencies", "design_sources",
        "display_mode", "mime_type", "render_tool", "requirements", "resource_uri",
        "supported_locales", "visual_qa",
    }
    if not isinstance(policy, dict) or set(policy) != required_keys:
        return ["policy.fields"]
    if policy.get("schema_version") != "hwpx-agent.p16-widget-shell-policy/v1" or policy.get("task") != "P16-04":
        errors.append("policy.identity")
    if policy.get("resource_uri") != "ui://hwpx-agent/document-work/v1.html":
        errors.append("policy.resource_uri")
    if policy.get("mime_type") != "text/html;profile=mcp-app":
        errors.append("policy.mime")
    if policy.get("render_tool") != "render_document_work_widget" or policy.get("display_mode") != "inline":
        errors.append("policy.render")
    if policy.get("requirements") != list(EXPECTED_REQUIREMENTS):
        errors.append("policy.requirements")
    if policy.get("supported_locales") != ["en-US", "ko-KR"]:
        errors.append("policy.locales")
    csp = policy.get("csp")
    if csp != {"connectDomains": [], "frameDomains": None, "resourceDomains": []}:
        errors.append("policy.csp")
    bundle = policy.get("bundle")
    if bundle != {
        "html": "web/plugin-widget/dist/widget-v1.html",
        "max_bytes": 700000,
        "preview_html": "web/plugin-widget/dist/preview.html",
    }:
        errors.append("policy.bundle")
    dependencies = policy.get("dependencies")
    if not isinstance(dependencies, list) or len(dependencies) != len(EXPECTED_DEPENDENCIES):
        errors.append("policy.dependencies")
    else:
        observed = {
            item.get("name"): (item.get("version"), item.get("scope"))
            for item in dependencies if isinstance(item, dict)
        }
        if observed != EXPECTED_DEPENDENCIES or any(
            not isinstance(item.get("integrity"), str) or not item["integrity"].startswith("sha512-")
            for item in dependencies if isinstance(item, dict)
        ):
            errors.append("policy.dependencies")
    design = policy.get("design_sources")
    if not isinstance(design, list) or len(design) != 2:
        errors.append("policy.design")
    else:
        expected_paths = {
            "implementation/p16/design/p16-04-widget-shell-desktop-concept.png": (1576, 998),
            "implementation/p16/design/p16-04-widget-shell-narrow-concept.png": (1024, 1536),
        }
        for item in design:
            if not isinstance(item, dict) or set(item) != {"bytes", "height", "path", "sha256", "width"}:
                errors.append("policy.design.entry")
                continue
            relative = item.get("path")
            if relative not in expected_paths:
                errors.append("policy.design.path")
                continue
            try:
                value = (root / relative).read_bytes()
            except OSError:
                errors.append("policy.design.read")
                continue
            width, height = expected_paths[relative]
            if (
                item.get("bytes") != len(value)
                or item.get("sha256") != sha256_bytes(value)
                or item.get("width") != width
                or item.get("height") != height
                or png_dimensions(value) != (width, height)
            ):
                errors.append("policy.design.digest")
    visual = policy.get("visual_qa")
    if (
        not isinstance(visual, dict)
        or set(visual) != {
            "browser", "capture_method", "captures", "concept_and_capture_inspection",
            "minimum_css_width",
        }
        or visual.get("browser") != "Google Chrome 152.0.7977.65"
        or visual.get("capture_method") != "isolated_headless_file_preview"
        or visual.get("concept_and_capture_inspection") != "view_image_original"
        or visual.get("minimum_css_width") != 320
    ):
        errors.append("policy.visual_qa")
    elif not isinstance(visual.get("captures"), list) or len(visual["captures"]) != 7:
        errors.append("policy.visual_qa.captures")
    else:
        expected_captures = {
            "implementation/p16/visual-qa/p16-04-desktop-approval.png": (1200, 720),
            "implementation/p16/visual-qa/p16-04-desktop-dark-ready.png": (1200, 720),
            "implementation/p16/visual-qa/p16-04-desktop-error.png": (1200, 720),
            "implementation/p16/visual-qa/p16-04-desktop-ready.png": (1200, 720),
            "implementation/p16/visual-qa/p16-04-narrow-approval.png": (500, 720),
            "implementation/p16/visual-qa/p16-04-narrow-error.png": (500, 720),
            "implementation/p16/visual-qa/p16-04-narrow-ready.png": (500, 720),
        }
        observed_paths: set[str] = set()
        for item in visual["captures"]:
            if not isinstance(item, dict) or set(item) != {"bytes", "height", "path", "sha256", "width"}:
                errors.append("policy.visual_qa.entry")
                continue
            relative = item.get("path")
            if not isinstance(relative, str) or relative not in expected_captures or relative in observed_paths:
                errors.append("policy.visual_qa.path")
                continue
            observed_paths.add(relative)
            try:
                value = (root / relative).read_bytes()
            except OSError:
                errors.append("policy.visual_qa.read")
                continue
            width, height = expected_captures[relative]
            if (
                item.get("bytes") != len(value)
                or item.get("sha256") != sha256_bytes(value)
                or item.get("width") != width
                or item.get("height") != height
                or png_dimensions(value) != (width, height)
            ):
                errors.append("policy.visual_qa.digest")
        if observed_paths != set(expected_captures):
            errors.append("policy.visual_qa.coverage")
    return sorted(set(errors))


def validate_dependencies(policy: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    package, package_errors = load_json(root / PACKAGE_PATH.relative_to(ROOT))
    errors.extend(f"package.{error}" for error in package_errors)
    if not isinstance(package, dict):
        return sorted(set(errors + ["package.object"]))
    runtime = package.get("dependencies")
    development = package.get("devDependencies")
    for item in policy["dependencies"]:
        scope = item["scope"]
        collection = runtime if scope == "runtime" else development
        if not isinstance(collection, dict) or collection.get(item["name"]) != item["version"]:
            errors.append(f"package.version:{item['name']}")
    try:
        lock_text = (root / LOCK_PATH.relative_to(ROOT)).read_text(encoding="utf-8")
    except OSError:
        return sorted(set(errors + ["lock.read"]))
    for item in policy["dependencies"]:
        if item["integrity"] not in lock_text:
            errors.append(f"lock.integrity:{item['name']}")
    try:
        workspace = (root / "pnpm-workspace.yaml").read_text(encoding="utf-8")
    except OSError:
        errors.append("workspace.read")
    else:
        if "  esbuild: true\n" not in workspace or '"@modelcontextprotocol/inspector": false\n' not in workspace:
            errors.append("workspace.allow_builds")
    return sorted(set(errors))


def validate_public_catalog(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    path = root / CATALOG_PATH.relative_to(ROOT)
    try:
        raw = path.read_bytes()
    except OSError:
        return ["catalog.read"]
    if sha256_bytes(raw) != EXPECTED_CATALOG_SHA256:
        errors.append("catalog.digest")
    catalog, parse_errors = load_json(path)
    errors.extend(f"catalog.{error}" for error in parse_errors)
    if not isinstance(catalog, dict) or not isinstance(catalog.get("tools"), list):
        return sorted(set(errors + ["catalog.tools"]))
    tools = catalog["tools"]
    names = tuple(sorted(tool.get("name") for tool in tools if isinstance(tool, dict)))
    if names != PUBLIC_TOOL_NAMES or len(tools) != 18:
        errors.append("catalog.names")
    if any(_contains_resource_uri(tool) for tool in tools):
        errors.append("catalog.ui_contamination")
    project_open = next((tool for tool in tools if isinstance(tool, dict) and tool.get("name") == "project_open"), None)
    if (
        not isinstance(project_open, dict)
        or project_open.get("annotations", {}).get("readOnlyHint") is not True
        or project_open.get("inputSchema", {}).get("additionalProperties") is not False
        or project_open.get("inputSchema", {}).get("required")
        != ["client_surface", "locale", "request_id", "project_id", "include"]
    ):
        errors.append("catalog.project_open")
    return sorted(set(errors))


def validate_authored_browser_sources(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    forbidden = re.compile(
        r"(?:\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\s*\(|\bEventSource\s*\(|"
        r"\bsendBeacon\s*\(|\.hostname\b|\.openExternal\s*\(|"
        r"\b(?:localStorage|sessionStorage)\b|document\.cookie|https?://)",
        re.IGNORECASE,
    )
    for relative in AUTHORED_BROWSER_SOURCES:
        path = root / relative
        try:
            value = path.read_bytes()
            text = value.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            errors.append(f"source.read:{relative}")
            continue
        if b"\r" in value or b"\x00" in value:
            errors.append(f"source.encoding:{relative}")
        if forbidden.search(text):
            errors.append(f"source.network_or_storage:{relative}")
    return sorted(set(errors))


def _relative_luminance(hex_color: str) -> float:
    channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first: str, second: str) -> float:
    bright, dark = sorted((_relative_luminance(first), _relative_luminance(second)), reverse=True)
    return (bright + 0.05) / (dark + 0.05)


def validate_css_contract(root: Path = ROOT) -> list[str]:
    try:
        text = (root / "web/plugin-widget/src/styles.css").read_text(encoding="utf-8")
    except OSError:
        return ["css.read"]
    errors: list[str] = []
    required_fragments = (
        "min-width: 320px", "@media (max-width: 719px)", "min-height: 44px",
        ":focus-visible", "prefers-reduced-motion: reduce", "--status: #117a4b",
        "--status: #9a5800", "--status: #c62d2d", "--status: #5bd19a",
        "--status: #f0ad4e", "--status: #ff7b7b", "--primary-contrast: #111722",
    )
    if any(fragment not in text for fragment in required_fragments):
        errors.append("css.required")
    pairs = (
        ("#117a4b", "#ffffff"), ("#9a5800", "#ffffff"), ("#c62d2d", "#ffffff"),
        ("#5bd19a", "#171f2c"), ("#f0ad4e", "#171f2c"), ("#ff7b7b", "#171f2c"),
        ("#111722", "#78aef7"),
    )
    if any(contrast_ratio(foreground, background) < 4.5 for foreground, background in pairs):
        errors.append("css.contrast")
    return errors


def validate_bundle_bytes(value: bytes, max_bytes: int = 700000) -> list[str]:
    errors: list[str] = []
    if not 1 <= len(value) <= max_bytes:
        errors.append("bundle.bytes")
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError:
        return sorted(set(errors + ["bundle.utf8"]))
    if "\r" in text or "\x00" in text:
        errors.append("bundle.encoding")
    if not text.startswith("<!doctype html>\n") or text.count('<div id="root"></div>') != 1:
        errors.append("bundle.html")
    if text.count("\n<script>") != 1 or text.count("</script>\n") != 1:
        errors.append("bundle.script")
    for index, pattern in enumerate(FORBIDDEN_BUNDLE_PATTERNS):
        if pattern.search(text):
            errors.append(f"bundle.forbidden:{index}")
    for required in (
        "ui/initialize", "ui/notifications/tool-input", "ui/notifications/tool-result",
        "ui/resource-teardown", "tools/call", "project_open", "approval_pending",
        "hwpx-agent.widget-render-request/v1", "hwpx-agent.widget-shell/v1",
    ):
        if required not in text:
            errors.append(f"bundle.protocol:{required}")
    return sorted(set(errors))


def validate_bundle(policy: dict[str, Any], root: Path = ROOT) -> tuple[dict[str, Any] | None, list[str]]:
    path = root / policy["bundle"]["html"]
    preview = root / policy["bundle"]["preview_html"]
    try:
        value = path.read_bytes()
        preview_value = preview.read_bytes()
    except OSError:
        return None, ["bundle.read"]
    errors = validate_bundle_bytes(value, policy["bundle"]["max_bytes"])
    if not 1 <= len(preview_value) <= policy["bundle"]["max_bytes"]:
        errors.append("preview.bytes")
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(value),
        "sha256": sha256_bytes(value),
        "preview_path": preview.relative_to(root).as_posix(),
        "preview_bytes": len(preview_value),
        "preview_sha256": sha256_bytes(preview_value),
    }, sorted(set(errors))


def validate_all(root: Path = ROOT) -> tuple[dict[str, Any] | None, list[str]]:
    policy, parse_errors = load_json(root / POLICY_PATH.relative_to(ROOT))
    errors = list(parse_errors)
    if not isinstance(policy, dict):
        return None, sorted(set(errors + ["policy.object"]))
    errors.extend(validate_policy(policy, root))
    errors.extend(validate_dependencies(policy, root))
    errors.extend(validate_public_catalog(root))
    errors.extend(validate_authored_browser_sources(root))
    errors.extend(validate_css_contract(root))
    bundle, bundle_errors = validate_bundle(policy, root)
    errors.extend(bundle_errors)
    return bundle, sorted(set(errors))
