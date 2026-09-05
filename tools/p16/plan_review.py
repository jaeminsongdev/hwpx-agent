from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import continuity

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "implementation/p16/p16-plan-review-policy-v1.json"
PREDECESSOR_PATH = ROOT / "implementation/p16/p16-continuity-contract-v1.json"
CATALOG_PATH = ROOT / "protocol/mcp/p15-public-tools-v1.json"
BUNDLE_PATH = ROOT / "web/plugin-widget/dist/plan-review-widget-v1.html"
PREVIEW_PATH = ROOT / "web/plugin-widget/dist/plan-review-preview.html"
HARNESS_PATH = ROOT / "web/plugin-widget/dist/plan-review-e2e-host.html"
EXPECTED_PREDECESSOR_SHA256 = "227be012d78ad9d055f85873096d4a3c3e3faebfde3e3de6f97d2efe8fc81e48"
EXPECTED_CATALOG_SHA256 = "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001"
EXPECTED_REQUIREMENTS = ("P16-R01", "P16-R02", "P16-R03", "P16-R04", "P16-R05", "P16-R06", "P16-R09", "P16-R10", "P16-R17", "P16-R26", "P16-R28", "P16-R29", "P16-R34")
PRODUCTION_SOURCES = (
    "web/plugin-widget/src/plan-review-component.tsx", "web/plugin-widget/src/plan-review-controller.ts",
    "web/plugin-widget/src/plan-review-mcp-app-port.ts", "web/plugin-widget/src/plan-review-model.ts",
    "web/plugin-widget/src/plan-review-resource.ts", "web/plugin-widget/src/plan-review-styles.css",
    "web/plugin-widget/src/plan-review-ui.tsx",
)

def validate_policy(policy: Any, root: Path = ROOT) -> list[str]:
    required_fields = {"schema_version", "task", "requirements", "resource", "render_tool", "server_calls", "bounds", "confirmation", "design_source", "visual_qa", "e2e"}
    if not isinstance(policy, dict) or set(policy) != required_fields:
        return ["policy.fields"]
    errors: list[str] = []
    if policy.get("schema_version") != "hwpx-agent.p16-plan-review-policy/v1" or policy.get("task") != "P16-06":
        errors.append("policy.identity")
    if policy.get("requirements") != list(EXPECTED_REQUIREMENTS):
        errors.append("policy.requirements")
    if policy.get("resource") != {"uri": "ui://hwpx-agent/plan-review/v1.html", "mime_type": "text/html;profile=mcp-app", "html": "web/plugin-widget/dist/plan-review-widget-v1.html", "max_bytes": 800000, "csp": {"connectDomains": [], "resourceDomains": []}}:
        errors.append("policy.resource")
    if policy.get("render_tool") != {"name": "render_plan_review_widget", "oauth_scopes": ["project.read"], "read_only": True}:
        errors.append("policy.render_tool")
    expected_calls = [
        {"name": "capability_check", "mode": "read", "oauth_scopes": ["project.read"]},
        {"name": "document_edit", "mode": "dry_run", "oauth_scopes": ["artifact.read", "artifact.write", "job.submit", "project.read", "project.write"]},
        {"name": "document_edit", "mode": "write_confirmed", "oauth_scopes": ["artifact.read", "artifact.write", "job.submit", "project.read", "project.write"]},
    ]
    if policy.get("server_calls") != expected_calls:
        errors.append("policy.calls")
    if policy.get("bounds") != {"capability_routes": 12, "diff_categories": 8, "warnings": 8, "primary_actions": 1, "secondary_actions": 1, "minimum_css_width": 320, "responsive_breakpoint": 720}:
        errors.append("policy.bounds")
    if policy.get("confirmation") != {"review_click": True, "explicit_acknowledgement": True, "final_click": True, "repeat_capability_check": True, "repeat_dry_run": True, "distinct_idempotency_keys": True, "host_confirmation_still_required": True}:
        errors.append("policy.confirmation")
    errors.extend(f"policy.design.{item}" for item in continuity.validate_image_entry(policy.get("design_source"), root, (1536, 1024)))
    expected_captures = {
        "implementation/p16/visual-qa/p16-06-desktop-blocked.png": (1200, 760),
        "implementation/p16/visual-qa/p16-06-desktop-confirm.png": (1200, 760),
        "implementation/p16/visual-qa/p16-06-desktop-dark-submitted.png": (1200, 760),
        "implementation/p16/visual-qa/p16-06-desktop-ready.png": (1200, 760),
        "implementation/p16/visual-qa/p16-06-narrow-blocked.png": (500, 1200),
        "implementation/p16/visual-qa/p16-06-narrow-confirm.png": (500, 1200),
        "implementation/p16/visual-qa/p16-06-narrow-ready.png": (500, 1200),
    }
    visual = policy.get("visual_qa")
    if not isinstance(visual, dict) or set(visual) != {"browser", "capture_method", "captures"} or visual.get("browser") != "Google Chrome 152.0.7977.76" or visual.get("capture_method") != "isolated_headless_file_preview" or not isinstance(visual.get("captures"), list) or len(visual["captures"]) != 7:
        errors.append("policy.visual")
    else:
        seen: set[str] = set()
        for item in visual["captures"]:
            relative = item.get("path") if isinstance(item, dict) else None
            if not isinstance(relative, str) or relative not in expected_captures or relative in seen:
                errors.append("policy.visual.path")
                continue
            seen.add(relative)
            errors.extend(f"policy.visual.{error}" for error in continuity.validate_image_entry(item, root, expected_captures[relative]))
        if seen != set(expected_captures):
            errors.append("policy.visual.coverage")
    if policy.get("e2e") != {"runner": "tools/p16/run_plan_review_e2e.py", "bridge": "real_ext_apps_appbridge_postmessage_iframe", "expected_calls": ["capability_check", "document_edit_dry", "capability_check", "document_edit_dry", "document_edit_execute"], "actual_host": False}:
        errors.append("policy.e2e")
    return sorted(set(errors))

def validate_predecessor(root: Path = ROOT) -> list[str]:
    path = root / PREDECESSOR_PATH.relative_to(ROOT)
    try:
        errors = [] if continuity.sha256_bytes(path.read_bytes()) == EXPECTED_PREDECESSOR_SHA256 else ["predecessor.digest"]
    except OSError:
        errors = ["predecessor.read"]
    if root == ROOT:
        _, predecessor_errors = continuity.validate_all(root)
        errors.extend(f"predecessor.validation:{error}" for error in predecessor_errors)
    return sorted(set(errors))

def validate_catalog(root: Path = ROOT) -> list[str]:
    path = root / CATALOG_PATH.relative_to(ROOT)
    try:
        raw = path.read_bytes()
    except OSError:
        return ["catalog.read"]
    errors = [] if continuity.sha256_bytes(raw) == EXPECTED_CATALOG_SHA256 else ["catalog.digest"]
    catalog, parse_errors = continuity.load_json(path)
    errors.extend(f"catalog.{error}" for error in parse_errors)
    if not isinstance(catalog, dict) or not isinstance(catalog.get("tools"), list):
        return sorted(set(errors + ["catalog.tools"]))
    tools = {item.get("name"): item for item in catalog["tools"] if isinstance(item, dict)}
    expected = {"capability_check": ([{"type": "oauth2", "scopes": ["project.read"]}], True), "document_edit": ([{"type": "oauth2", "scopes": ["artifact.read", "artifact.write", "job.submit", "project.read", "project.write"]}], False)}
    for name, (security, read_only) in expected.items():
        tool = tools.get(name)
        if not isinstance(tool, dict) or tool.get("securitySchemes") != security or tool.get("_meta", {}).get("securitySchemes") != security or tool.get("annotations", {}).get("readOnlyHint") is not read_only or tool.get("inputSchema", {}).get("additionalProperties") is not False or tool.get("outputSchema", {}).get("additionalProperties") is not False:
            errors.append(f"catalog.tool:{name}")
    return sorted(set(errors))

def validate_sources(root: Path = ROOT) -> list[str]:
    forbidden = re.compile(r"(?:\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\s*\(|\bEventSource\s*\(|\bsendBeacon\s*\(|\.hostname\b|\.openExternal\s*\(|\b(?:localStorage|sessionStorage)\b|document\.cookie|https?://|HAction\.|HWPFrame\.|<hp:)", re.IGNORECASE)
    errors: list[str] = []
    for relative in PRODUCTION_SOURCES:
        try:
            raw = (root / relative).read_bytes(); text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            errors.append(f"source.read:{relative}"); continue
        if b"\r" in raw or b"\x00" in raw:
            errors.append(f"source.encoding:{relative}")
        if forbidden.search(text):
            errors.append(f"source.forbidden:{relative}")
    return sorted(set(errors))

def validate_css(root: Path = ROOT) -> list[str]:
    try:
        text = (root / "web/plugin-widget/src/plan-review-styles.css").read_text(encoding="utf-8")
    except OSError:
        return ["css.read"]
    required = ("min-width: 320px", "@media (max-width: 719px)", "min-height: 44px", ":focus-visible", "prefers-reduced-motion: reduce", "--green: #117a4b", "--amber: #8a4b00", "--red: #b42318", "--green: #5bd19a", "--amber: #f0ad4e", "--red: #ff8a80")
    errors = ["css.required"] if any(value not in text for value in required) else []
    pairs = (("#117a4b", "#ffffff"), ("#8a4b00", "#ffffff"), ("#b42318", "#ffffff"), ("#5bd19a", "#171f2c"), ("#f0ad4e", "#171f2c"), ("#ff8a80", "#171f2c"))
    if any(continuity.contrast_ratio(foreground, background) < 4.5 for foreground, background in pairs):
        errors.append("css.contrast")
    return errors

def validate_bundle_bytes(value: bytes, max_bytes: int = 800000) -> list[str]:
    errors: list[str] = []
    if not 1 <= len(value) <= max_bytes:
        errors.append("bundle.bytes")
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError:
        return errors + ["bundle.utf8"]
    for index, pattern in enumerate(continuity.FORBIDDEN_BUNDLE_PATTERNS):
        if pattern.search(text):
            errors.append(f"bundle.forbidden:{index}")
    for required in ("ui/initialize", "ui/notifications/tool-input", "ui/notifications/tool-result", "tools/call", "capability_check", "document_edit", "hwpx-agent.plan-review-render-request/v1", "hwpx-agent.plan-review/v1", "confirm_execution"):
        if required not in text:
            errors.append(f"bundle.protocol:{required}")
    return sorted(set(errors))

def validate_bundles(policy: dict[str, Any], root: Path = ROOT) -> tuple[dict[str, Any] | None, list[str]]:
    paths = {"resource": root / policy["resource"]["html"], "preview": root / PREVIEW_PATH.relative_to(ROOT), "harness": root / HARNESS_PATH.relative_to(ROOT)}
    try:
        values = {name: path.read_bytes() for name, path in paths.items()}
    except OSError:
        return None, ["bundle.read"]
    errors = validate_bundle_bytes(values["resource"], policy["resource"]["max_bytes"])
    if not 1 <= len(values["preview"]) <= policy["resource"]["max_bytes"]:
        errors.append("preview.bytes")
    harness = values["harness"].decode("utf-8", errors="replace")
    required = ("ui/initialize", "tools/call", "PASS calls=5 order=capability_check,document_edit(dry),capability_check,document_edit(dry),document_edit(execute)")
    if any(value not in harness for value in required):
        errors.append("harness.required")
    bundles = {name: {"path": paths[name].relative_to(root).as_posix(), "bytes": len(value), "sha256": continuity.sha256_bytes(value)} for name, value in values.items()}
    return bundles, sorted(set(errors))

def validate_all(root: Path = ROOT) -> tuple[dict[str, Any] | None, list[str]]:
    policy, parse_errors = continuity.load_json(root / POLICY_PATH.relative_to(ROOT))
    errors = list(parse_errors)
    if not isinstance(policy, dict):
        return None, sorted(set(errors + ["policy.object"]))
    errors.extend(validate_policy(policy, root)); errors.extend(validate_predecessor(root)); errors.extend(validate_catalog(root)); errors.extend(validate_sources(root)); errors.extend(continuity.validate_evidence_ignore(root)); errors.extend(validate_css(root))
    bundles, bundle_errors = validate_bundles(policy, root); errors.extend(bundle_errors)
    return bundles, sorted(set(errors))
