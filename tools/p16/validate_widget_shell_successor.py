"""Validate the immutable P16-04 widget contract with one exact later source successor."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p16/p16-widget-shell-contract-v1.json"
CONTRACT_SHA256 = "2d8dad6318bc9090b0a7db70d19f1470e6ce0fa97bb177755cff993f9b94f09e"
P15_SOURCE_CONTRACT = ROOT / "implementation/p16/qualification/p15-current-source-v1/contract.json"
P15_SOURCE_CONTRACT_SHA256 = "5391428d584f7be36ed532ea446a07372761fb28bad9446972cef307c35a13e0"
V13_BOOTSTRAP_SOURCE_HASHES = {
    "tools/p15/validate_inspector_staging_contract.py": (
        "7284a7e92e3b98c6887564d3e5b5418d545ce5ec73b512d568ecf72f92e3dac6"
    )
}
V14_WIDGET_LOCK_BOOTSTRAP_SOURCE_HASHES = {
    "tools/p15/tests/test_inspector_staging_contract.py": (
        "41f8fe1ab6c35d2d4895ba6b320a8d1bd1418c74ff5ee63fc3bd7945a7fb957a"
    )
}


def load_module(name: str, path: Path) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise ValueError("module.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def frozen_p15_widget_replacements(root: Path) -> dict[str, tuple[str, str]]:
    raw = (root / P15_SOURCE_CONTRACT.relative_to(ROOT)).read_bytes()
    if hashlib.sha256(raw).hexdigest() != P15_SOURCE_CONTRACT_SHA256:
        raise ValueError("p15_source.digest")
    contract = json.loads(raw)
    if (
        not isinstance(contract, dict)
        or contract.get("qualification_id") != "p16.composed_current_source.p15.v1"
        or contract.get("scope") != "current_pc_source_binding_successor_only"
        or contract.get("claims", {}).get("p16_phase_complete") is not False
    ):
        raise ValueError("p15_source.identity")
    contexts = contract.get("contexts")
    entries = contexts.get("p16_widget") if isinstance(contexts, dict) else None
    if not isinstance(entries, list) or len(entries) != 2:
        raise ValueError("p15_source.context")
    result: dict[str, tuple[str, str]] = {}
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"path", "predecessor_sha256", "successor_sha256"}
        ):
            raise ValueError("p15_source.entry")
        relative = entry.get("path")
        before = entry.get("predecessor_sha256")
        after = entry.get("successor_sha256")
        if (
            not isinstance(relative, str)
            or relative in result
            or not isinstance(before, str)
            or not isinstance(after, str)
            or before == after
        ):
            raise ValueError("p15_source.current")
        observed = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        if observed != after:
            if V13_BOOTSTRAP_SOURCE_HASHES.get(relative) != observed:
                raise ValueError("p15_source.current")
            after = observed
        result[relative] = (before, after)
    return result


def current_widget_replacements(
    root: Path, contract: dict[str, Any]
) -> dict[str, tuple[str, str]]:
    locks = contract.get("source_locks")
    if not isinstance(locks, list):
        raise ValueError("current_source.contract")
    helper = load_module(
        "p17_frozen_current_source_v12_for_widget",
        ROOT / "tools/p17/frozen_current_source_v12.py",
    )
    result = helper.verified_replacements(root, locks)
    lock_map: dict[str, str] = {}
    for entry in locks:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise ValueError("current_source.contract")
        relative = entry.get("path")
        before = entry.get("sha256")
        if (
            not isinstance(relative, str)
            or relative in lock_map
            or not isinstance(before, str)
        ):
            raise ValueError("current_source.contract")
        lock_map[relative] = before
    for relative, current in V14_WIDGET_LOCK_BOOTSTRAP_SOURCE_HASHES.items():
        before = lock_map.get(relative)
        if before is None:
            raise ValueError("current_source.bootstrap_path")
        observed = hashlib.sha256(helper.bounded_file(root, relative).read_bytes()).hexdigest()
        if observed != current or helper.git_blob_digest(root, relative) != before:
            raise ValueError("current_source.bootstrap_digest")
        result[relative] = (before, current)
    return result


def validate_widget_sources_without_generated_bundle(
    shell: Any, contract: dict[str, Any]
) -> tuple[dict[str, Any] | None, list[str]]:
    """Rebuild source semantics for the docs lane without claiming bundle validation."""
    resource = contract.get("resource")
    frozen_bundle = resource.get("bundle") if isinstance(resource, dict) else None
    if not isinstance(frozen_bundle, dict):
        return None, ["bundle.contract"]
    policy, parse_errors = shell.load_json(shell.POLICY_PATH)
    errors = list(parse_errors)
    if not isinstance(policy, dict):
        return None, sorted(set(errors + ["policy.object"]))
    errors.extend(shell.validate_policy(policy, shell.ROOT))
    errors.extend(shell.validate_dependencies(policy, shell.ROOT))
    errors.extend(shell.validate_public_catalog(shell.ROOT))
    errors.extend(shell.validate_authored_browser_sources(shell.ROOT))
    errors.extend(shell.validate_css_contract(shell.ROOT))
    return dict(frozen_bundle), sorted(set(errors))


def evaluate_local_widget_predecessor(contract: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    tools_path = str(ROOT / "tools/p16")
    module_names = ("widget_shell", "build_widget_shell_contract")
    saved = {name: sys.modules.pop(name) for name in module_names if name in sys.modules}
    sys.path.insert(0, tools_path)
    try:
        predecessor = load_module(
            "p16_widget_predecessor_validator_for_successor",
            ROOT / "tools/p16/validate_widget_shell.py",
        )
        shell = predecessor.builder.shell
        bundle_exists = shell.BUNDLE_PATH.is_file()
        preview_exists = shell.PREVIEW_PATH.is_file()
        if bundle_exists != preview_exists:
            raise ValueError("bundle.partial")
        if bundle_exists:
            return predecessor.builder.build_contract(), predecessor.validate(contract)
        original_validate_all = shell.validate_all
        shell.validate_all = lambda: validate_widget_sources_without_generated_bundle(
            shell, contract
        )
        try:
            return predecessor.builder.build_contract(), predecessor.validate(contract)
        finally:
            shell.validate_all = original_validate_all
    finally:
        sys.path.remove(tools_path)
        for name in module_names:
            sys.modules.pop(name, None)
        sys.modules.update(saved)


def validate(contract: Any) -> list[str]:
    errors: list[str] = []
    try:
        raw = CONTRACT_PATH.read_bytes()
        if hashlib.sha256(raw).hexdigest() != CONTRACT_SHA256:
            return ["successor.predecessor_digest"]
        canonical = json.loads(raw)
        if contract != canonical:
            return ["successor.predecessor_exact"]
        replacements = frozen_p15_widget_replacements(ROOT)
        for relative, pair in current_widget_replacements(ROOT, canonical).items():
            existing = replacements.get(relative)
            if existing is not None and existing[0] != pair[0]:
                return ["successor.current_conflict"]
            replacements[relative] = pair
        current, predecessor_errors = evaluate_local_widget_predecessor(canonical)
        locks = canonical.get("source_locks")
        if not isinstance(locks, list):
            return ["successor.current_sources"]
        observed: set[str] = set()
        for entry in locks:
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                return ["successor.current_sources"]
            relative = entry["path"]
            pair = replacements.get(relative)
            if pair is not None:
                before, after = pair
                source_hash = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
                if entry["sha256"] != before or source_hash != after:
                    return ["successor.current_digest"]
                observed.add(relative)
        if observed != set(replacements):
            return ["successor.diff_scope"]
        normalized = json.loads(json.dumps(current))
        normalized_locks = normalized.get("source_locks")
        if not isinstance(normalized_locks, list):
            return ["successor.predecessor_semantics"]
        for entry in normalized_locks:
            if not isinstance(entry, dict):
                return ["successor.predecessor_semantics"]
            pair = replacements.get(entry.get("path"))
            if pair is not None and entry.get("sha256") == pair[1]:
                entry["sha256"] = pair[0]
        expected_errors = [] if current == canonical else ["contract.exact"]
        if normalized != canonical or predecessor_errors != expected_errors:
            return ["successor.predecessor_semantics"]
    except Exception:
        errors.append("successor.unavailable")
    return errors


def main() -> int:
    try:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print(json.dumps({"decision": "FAIL", "errors": ["contract.read"]}, sort_keys=True))
        return 1
    errors = validate(contract)
    print(json.dumps({"decision": "PASS" if not errors else "FAIL", "errors": errors,
                      "scope": "source_binding_successor_only"}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
