#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as error:
    print(f"required dependency missing: {error}", file=sys.stderr)
    raise SystemExit(2) from error

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "protocol" / "json-schema"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_fixture_content(manifest: dict, errors: list[str]) -> None:
    relative = PurePosixPath(manifest["content"]["path"])
    if relative.is_absolute() or ".." in relative.parts:
        errors.append(f"fixture path escapes repository: {relative}")
        return
    path = ROOT.joinpath(*relative.parts)
    if not path.is_file():
        errors.append(f"fixture content missing: {relative}")
        return
    content = path.read_bytes()
    actual_hash = hashlib.sha256(content).hexdigest()
    if actual_hash != manifest["content"]["sha256"]:
        errors.append(f"fixture checksum mismatch: {relative}")
    if len(content) != manifest["content"]["size_bytes"]:
        errors.append(f"fixture size mismatch: {relative}")


def main() -> int:
    errors: list[str] = []
    schemas: dict[str, dict] = {}
    for path in sorted(SCHEMA_ROOT.glob("*.schema.json")):
        schema = load(path)
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as error:  # jsonschema provides heterogeneous validation errors
            errors.append(f"schema compile failed {path.name}: {error}")
            continue
        schemas[path.name] = schema

    fixture_schema = schemas.get("fixture-manifest.schema.json")
    if fixture_schema is None:
        errors.append("fixture manifest schema missing")
    else:
        validator = Draft202012Validator(fixture_schema, format_checker=FormatChecker())
        manifests = sorted((ROOT / "fixtures").glob("**/*.fixture.json"))
        if not manifests:
            errors.append("no fixture manifests found")
        for path in manifests:
            manifest = load(path)
            violations = sorted(validator.iter_errors(manifest), key=lambda item: list(item.path))
            errors.extend(f"fixture {path.relative_to(ROOT)}: {violation.message}" for violation in violations)
            if not violations:
                validate_fixture_content(manifest, errors)

        valid = load(ROOT / "fixtures" / "synthetic" / "p01-foundation.fixture.json")
        negatives = {
            "missing_license": {key: value for key, value in valid.items() if key != "license"},
            "missing_privacy": {key: value for key, value in valid.items() if key != "privacy"},
            "private_redistribution": {
                **valid,
                "kind": "licensed_private",
                "license": {**valid["license"], "redistribution_allowed": True},
                "privacy": {**valid["privacy"], "retention": "restricted_local"},
            },
            "private_repository_retention": {
                **valid,
                "kind": "licensed_private",
                "license": {**valid["license"], "redistribution_allowed": False},
                "privacy": {**valid["privacy"], "retention": "repository"},
            },
        }
        for name, candidate in negatives.items():
            if validator.is_valid(candidate):
                errors.append(f"negative fixture unexpectedly valid: {name}")

    proto = (ROOT / "protocol" / "proto" / "hwpx_agent" / "foundation" / "v1" / "foundation.proto").read_text(encoding="utf-8")
    for forbidden in ("bytes document", "HAction", "ParameterSet", "raw_action"):
        if forbidden in proto:
            errors.append(f"forbidden public protocol surface: {forbidden}")
    for required in ("ArtifactRef", "WorkerRequestContext", "ValidationState"):
        if required not in proto:
            errors.append(f"protocol contract missing: {required}")

    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    action_lock = load(ROOT / "security" / "github-actions.lock.json")["actions"]
    locked_shas = set(action_lock.values())
    action_refs = re.findall(r"uses:\s*([^@\s]+)@([^\s#]+)", workflow)
    if not action_refs:
        errors.append("CI workflow contains no action references")
    for action, revision in action_refs:
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            errors.append(f"GitHub Action is not pinned by full SHA: {action}@{revision}")
        elif revision not in locked_shas:
            errors.append(f"GitHub Action SHA missing from lock: {action}@{revision}")
    for job in ("linux-core", "windows-worker", "widget", "docs", "security"):
        if not re.search(rf"^  {re.escape(job)}:\s*$", workflow, flags=re.MULTILINE):
            errors.append(f"CI job missing: {job}")
    if "continue-on-error: true" in workflow:
        errors.append("CI workflow must not weaken a gate with continue-on-error")

    print(json.dumps({"schemas": len(schemas), "fixture_manifests": len(list((ROOT / 'fixtures').glob('**/*.fixture.json'))), "pinned_action_references": len(action_refs), "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
