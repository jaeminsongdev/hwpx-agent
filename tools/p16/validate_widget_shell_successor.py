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


def load_module(name: str, path: Path) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise ValueError("module.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def load_shared_qualification() -> Any:
    path = (ROOT / "tools/p16/p15_source_qualification.py").resolve()
    name = "_hwpx_agent_p16_p15_source_qualification"
    module = sys.modules.get(name)
    if module is not None and Path(str(getattr(module, "__file__", ""))).resolve() == path:
        return module
    sys.modules.pop(name, None)
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise ValueError("qualification.load")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    try:
        specification.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def load_current_source_qualification() -> Any:
    path = (ROOT / "tools/p17/current_workspace_source_qualification.py").resolve()
    specification = importlib.util.spec_from_file_location(
        "p17_current_source_for_widget_successor", path
    )
    if specification is None or specification.loader is None:
        raise ValueError("current_source.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def current_widget_replacements(
    root: Path, contract: dict[str, Any]
) -> dict[str, tuple[str, str]]:
    locks = contract.get("source_locks")
    if not isinstance(locks, list):
        raise ValueError("current_source.contract")
    successors = load_current_source_qualification().verified_successors(root)
    result: dict[str, tuple[str, str]] = {}
    for entry in locks:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise ValueError("current_source.contract")
        relative = entry["path"]
        before = entry["sha256"]
        successor = successors.get(relative)
        if successor is None:
            continue
        after = successor.get("current_sha256")
        accepted = successor.get("accepted_predecessor_sha256s")
        if not isinstance(after, str) or not isinstance(accepted, list) or before not in accepted:
            raise ValueError("current_source.pair")
        if hashlib.sha256((root / relative).read_bytes()).hexdigest() != after:
            raise ValueError("current_source.digest")
        result[relative] = (before, after)
    return result


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
        return predecessor.builder.build_contract(), predecessor.validate(contract)
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
        qualification = load_shared_qualification()
        replacements = qualification.verified_widget_replacements(ROOT)
        for relative, pair in current_widget_replacements(ROOT, canonical).items():
            existing = replacements.get(relative)
            if existing is not None and existing != pair:
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
