from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct
from typing import Any

import widget_shell


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "implementation/p16/p16-continuity-policy-v1.json"
PREDECESSOR_PATH = ROOT / "implementation/p16/p16-widget-shell-contract-v1.json"
CATALOG_PATH = ROOT / "protocol/mcp/p15-public-tools-v1.json"
BUNDLE_PATH = ROOT / "web/plugin-widget/dist/continuity-widget-v1.html"
PREVIEW_PATH = ROOT / "web/plugin-widget/dist/continuity-preview.html"
HARNESS_PATH = ROOT / "web/plugin-widget/dist/continuity-e2e-host.html"
EVIDENCE_IGNORE_ENTRY = "/artifacts/"
EXPECTED_PREDECESSOR_SHA256 = "2d8dad6318bc9090b0a7db70d19f1470e6ce0fa97bb177755cff993f9b94f09e"
EXPECTED_CATALOG_SHA256 = "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001"
EXPECTED_REQUIREMENTS = (
    "P16-R01", "P16-R02", "P16-R03", "P16-R04", "P16-R05", "P16-R06",
    "P16-R09", "P16-R10", "P16-R17", "P16-R26", "P16-R28", "P16-R34",
)
EXPECTED_CALLS = {
    "project_open": ("read", ("project.read",), True),
    "project_history": ("read", ("project.read",), True),
    "project_checkpoint": ("write_confirmed", ("project.read", "project.write"), False),
}
PRODUCTION_BROWSER_SOURCES = (
    "web/plugin-widget/src/continuity-component.tsx",
    "web/plugin-widget/src/continuity-controller.ts",
    "web/plugin-widget/src/continuity-mcp-app-port.ts",
    "web/plugin-widget/src/continuity-model.ts",
    "web/plugin-widget/src/continuity-resource.ts",
    "web/plugin-widget/src/continuity-styles.css",
    "web/plugin-widget/src/continuity-ui.tsx",
)
FORBIDDEN_BUNDLE_PATTERNS = (
    re.compile(r"new\s+Function\b"),
    re.compile(r"(?<![A-Za-z])eval\s*\("),
    re.compile(r"<(?:base|embed|form|iframe|object)\b", re.IGNORECASE),
    re.compile(r"(?:localStorage|sessionStorage|document\.cookie)"),
    re.compile(r"(?:[A-Z]:\\|Authorization:\s*Bearer|HAction\.|HWPFrame\.)"),
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> tuple[Any | None, list[str]]:
    try:
        raw = path.read_bytes()
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_pairs), []
    except OSError:
        return None, ["json.read"]
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None, ["json.parse"]


def png_dimensions(value: bytes) -> tuple[int, int] | None:
    if len(value) < 24 or value[:8] != b"\x89PNG\r\n\x1a\n" or value[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", value[16:24])


def validate_image_entry(item: Any, root: Path, expected: tuple[int, int]) -> list[str]:
    if not isinstance(item, dict) or set(item) != {"path", "bytes", "width", "height", "sha256"}:
        return ["image.fields"]
    relative = item.get("path")
    if not isinstance(relative, str):
        return ["image.path"]
    try:
        value = (root / relative).read_bytes()
    except OSError:
        return ["image.read"]
    width, height = expected
    if (
        item.get("bytes") != len(value)
        or item.get("width") != width
        or item.get("height") != height
        or item.get("sha256") != sha256_bytes(value)
        or png_dimensions(value) != (width, height)
    ):
        return ["image.digest"]
    return []


def validate_policy(policy: Any, root: Path = ROOT) -> list[str]:
    if not isinstance(policy, dict) or set(policy) != {
        "schema_version", "task", "requirements", "resource", "render_tool",
        "server_calls", "bounds", "design_source", "visual_qa", "e2e",
    }:
        return ["policy.fields"]
    errors: list[str] = []
    if policy.get("schema_version") != "hwpx-agent.p16-continuity-policy/v1" or policy.get("task") != "P16-05":
        errors.append("policy.identity")
    if policy.get("requirements") != list(EXPECTED_REQUIREMENTS):
        errors.append("policy.requirements")
    if policy.get("resource") != {
        "uri": "ui://hwpx-agent/project-continuity/v1.html",
        "mime_type": "text/html;profile=mcp-app",
        "html": "web/plugin-widget/dist/continuity-widget-v1.html",
        "max_bytes": 800000,
        "csp": {"connectDomains": [], "resourceDomains": []},
    }:
        errors.append("policy.resource")
    if policy.get("render_tool") != {
        "name": "render_project_continuity_widget",
        "oauth_scopes": ["project.read"],
        "read_only": True,
    }:
        errors.append("policy.render_tool")
    calls = policy.get("server_calls")
    if not isinstance(calls, list) or len(calls) != 3:
        errors.append("policy.calls")
    else:
        observed = {
            item.get("name"): (item.get("mode"), tuple(item.get("oauth_scopes", [])))
            for item in calls if isinstance(item, dict)
        }
        expected = {name: (mode, scopes) for name, (mode, scopes, _) in EXPECTED_CALLS.items()}
        if observed != expected:
            errors.append("policy.calls")
    if policy.get("bounds") != {
        "snapshot_revisions": 12,
        "rendered_revisions": 6,
        "primary_actions": 1,
        "secondary_actions": 1,
        "minimum_css_width": 320,
        "responsive_breakpoint": 720,
    }:
        errors.append("policy.bounds")
    design = policy.get("design_source")
    errors.extend(f"policy.design.{error}" for error in validate_image_entry(design, root, (1536, 1024)))
    visual = policy.get("visual_qa")
    expected_captures = {
        "implementation/p16/visual-qa/p16-05-desktop-confirm.png": (1200, 720),
        "implementation/p16/visual-qa/p16-05-desktop-conflict.png": (1200, 720),
        "implementation/p16/visual-qa/p16-05-desktop-dark-saved.png": (1200, 720),
        "implementation/p16/visual-qa/p16-05-desktop-ready.png": (1200, 720),
        "implementation/p16/visual-qa/p16-05-narrow-confirm.png": (500, 760),
        "implementation/p16/visual-qa/p16-05-narrow-conflict.png": (500, 760),
        "implementation/p16/visual-qa/p16-05-narrow-ready.png": (500, 760),
    }
    if (
        not isinstance(visual, dict)
        or set(visual) != {"browser", "capture_method", "captures"}
        or visual.get("browser") != "Google Chrome 152.0.7977.76"
        or visual.get("capture_method") != "isolated_headless_file_preview"
        or not isinstance(visual.get("captures"), list)
        or len(visual["captures"]) != 7
    ):
        errors.append("policy.visual")
    else:
        observed_paths: set[str] = set()
        for item in visual["captures"]:
            relative = item.get("path") if isinstance(item, dict) else None
            if not isinstance(relative, str) or relative not in expected_captures or relative in observed_paths:
                errors.append("policy.visual.path")
                continue
            observed_paths.add(relative)
            errors.extend(
                f"policy.visual.{error}" for error in validate_image_entry(item, root, expected_captures[relative])
            )
        if observed_paths != set(expected_captures):
            errors.append("policy.visual.coverage")
    if policy.get("e2e") != {
        "runner": "tools/p16/run_continuity_e2e.py",
        "bridge": "real_ext_apps_appbridge_postmessage_iframe",
        "expected_calls": ["project_open", "project_history", "project_checkpoint"],
        "actual_host": False,
    }:
        errors.append("policy.e2e")
    return sorted(set(errors))


def validate_predecessor(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        if sha256_bytes((root / PREDECESSOR_PATH.relative_to(ROOT)).read_bytes()) != EXPECTED_PREDECESSOR_SHA256:
            errors.append("predecessor.digest")
    except OSError:
        errors.append("predecessor.read")
    if root == ROOT:
        _, shell_errors = widget_shell.validate_all(root)
        errors.extend(f"predecessor.validation:{error}" for error in shell_errors)
    return sorted(set(errors))


def validate_public_catalog(root: Path = ROOT) -> list[str]:
    path = root / CATALOG_PATH.relative_to(ROOT)
    try:
        raw = path.read_bytes()
    except OSError:
        return ["catalog.read"]
    errors: list[str] = []
    if sha256_bytes(raw) != EXPECTED_CATALOG_SHA256:
        errors.append("catalog.digest")
    catalog, parse_errors = load_json(path)
    errors.extend(f"catalog.{error}" for error in parse_errors)
    if not isinstance(catalog, dict) or not isinstance(catalog.get("tools"), list):
        return sorted(set(errors + ["catalog.tools"]))
    by_name = {
        item.get("name"): item for item in catalog["tools"]
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    for name, (_, scopes, read_only) in EXPECTED_CALLS.items():
        tool = by_name.get(name)
        expected_security = [{"type": "oauth2", "scopes": list(scopes)}]
        if (
            not isinstance(tool, dict)
            or tool.get("securitySchemes") != expected_security
            or tool.get("_meta", {}).get("securitySchemes") != expected_security
            or tool.get("annotations", {}).get("readOnlyHint") is not read_only
            or tool.get("annotations", {}).get("destructiveHint") is not False
            or tool.get("inputSchema", {}).get("additionalProperties") is not False
            or tool.get("outputSchema", {}).get("additionalProperties") is not False
        ):
            errors.append(f"catalog.tool:{name}")
    return sorted(set(errors))


def validate_authored_sources(root: Path = ROOT) -> list[str]:
    forbidden = re.compile(
        r"(?:\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\s*\(|\bEventSource\s*\(|"
        r"\bsendBeacon\s*\(|\.hostname\b|\.openExternal\s*\(|"
        r"\b(?:localStorage|sessionStorage)\b|document\.cookie|https?://|"
        r"HAction\.|HWPFrame\.|<hp:)",
        re.IGNORECASE,
    )
    errors: list[str] = []
    for relative in PRODUCTION_BROWSER_SOURCES:
        try:
            raw = (root / relative).read_bytes()
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            errors.append(f"source.read:{relative}")
            continue
        if b"\r" in raw or b"\x00" in raw:
            errors.append(f"source.encoding:{relative}")
        if forbidden.search(text):
            errors.append(f"source.forbidden:{relative}")
    return sorted(set(errors))


def validate_evidence_ignore(root: Path = ROOT) -> list[str]:
    try:
        lines = (root / ".gitignore").read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return ["evidence_ignore.read"]
    return [] if EVIDENCE_IGNORE_ENTRY in lines else ["evidence_ignore.missing"]


def _relative_luminance(color: str) -> float:
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first: str, second: str) -> float:
    bright, dark = sorted((_relative_luminance(first), _relative_luminance(second)), reverse=True)
    return (bright + 0.05) / (dark + 0.05)


def validate_css(root: Path = ROOT) -> list[str]:
    try:
        text = (root / "web/plugin-widget/src/continuity-styles.css").read_text(encoding="utf-8")
    except OSError:
        return ["css.read"]
    required = (
        "min-width: 320px", "@media (max-width: 719px)", "min-height: 44px",
        ":focus-visible", "prefers-reduced-motion: reduce", "--status: #117a4b",
        "--warning: #8a4b00", "--status: #b42318", "--status: #5bd19a",
        "--warning: #f0ad4e", "--status: #ff8a80",
    )
    errors = ["css.required"] if any(item not in text for item in required) else []
    pairs = (
        ("#117a4b", "#ffffff"), ("#8a4b00", "#ffffff"), ("#b42318", "#ffffff"),
        ("#5bd19a", "#171f2c"), ("#f0ad4e", "#171f2c"), ("#ff8a80", "#171f2c"),
        ("#111722", "#78aef7"),
    )
    if any(contrast_ratio(foreground, background) < 4.5 for foreground, background in pairs):
        errors.append("css.contrast")
    return errors


def validate_bundle_bytes(value: bytes, max_bytes: int = 800000) -> list[str]:
    errors: list[str] = []
    if not 1 <= len(value) <= max_bytes:
        errors.append("bundle.bytes")
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError:
        return sorted(set(errors + ["bundle.utf8"]))
    if "\r" in text or "\x00" in text or not text.startswith("<!doctype html>\n"):
        errors.append("bundle.encoding_or_html")
    for index, pattern in enumerate(FORBIDDEN_BUNDLE_PATTERNS):
        if pattern.search(text):
            errors.append(f"bundle.forbidden:{index}")
    for required in (
        "ui/initialize", "ui/notifications/tool-input", "ui/notifications/tool-result",
        "tools/call", "project_open", "project_history", "project_checkpoint",
        "hwpx-agent.continuity-render-request/v1", "hwpx-agent.project-continuity/v1",
        "confirm_checkpoint",
    ):
        if required not in text:
            errors.append(f"bundle.protocol:{required}")
    return sorted(set(errors))


def validate_bundles(policy: dict[str, Any], root: Path = ROOT) -> tuple[dict[str, Any] | None, list[str]]:
    paths = {
        "resource": root / policy["resource"]["html"],
        "preview": root / PREVIEW_PATH.relative_to(ROOT),
        "harness": root / HARNESS_PATH.relative_to(ROOT),
    }
    values: dict[str, bytes] = {}
    try:
        values = {name: path.read_bytes() for name, path in paths.items()}
    except OSError:
        return None, ["bundle.read"]
    errors = validate_bundle_bytes(values["resource"], policy["resource"]["max_bytes"])
    if not 1 <= len(values["preview"]) <= policy["resource"]["max_bytes"]:
        errors.append("preview.bytes")
    harness_text = values["harness"].decode("utf-8", errors="replace")
    for required in (
        "ui/initialize", "tools/call",
        "PASS calls=3 order=project_open,project_history,project_checkpoint",
    ):
        if required not in harness_text:
            errors.append(f"harness.required:{required}")
    return {
        name: {
            "path": paths[name].relative_to(root).as_posix(),
            "bytes": len(value),
            "sha256": sha256_bytes(value),
        }
        for name, value in values.items()
    }, sorted(set(errors))


def validate_all(root: Path = ROOT) -> tuple[dict[str, Any] | None, list[str]]:
    policy, parse_errors = load_json(root / POLICY_PATH.relative_to(ROOT))
    errors = list(parse_errors)
    if not isinstance(policy, dict):
        return None, sorted(set(errors + ["policy.object"]))
    errors.extend(validate_policy(policy, root))
    errors.extend(validate_predecessor(root))
    errors.extend(validate_public_catalog(root))
    errors.extend(validate_authored_sources(root))
    errors.extend(validate_evidence_ignore(root))
    errors.extend(validate_css(root))
    bundles, bundle_errors = validate_bundles(policy, root)
    errors.extend(bundle_errors)
    return bundles, sorted(set(errors))
