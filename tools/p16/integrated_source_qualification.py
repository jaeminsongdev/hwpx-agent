"""Exact MAIN/P16 source successor; never a phase, host, or production waiver."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MAIN_PARENT = "9cc1db3b222a8e8f2b79ebf9ade7e3c8d6813a98"
P16_PARENT = "62542b0e0126f0687f97fcb2c1357c3600d87fdf"
BASE = "implementation/p16/qualification/main-9cc1-p16-62542-v1"
CONTRACT_PATH = f"{BASE}/contract.json"
POSTGRES_CONTRACT = "implementation/p16/qualification/postgres-217ba56/contract.json"
POSTGRES_CONTRACT_SHA256 = "c37e5b773a9117ffdb4af40c95d1263e08fdf7f6e25c69c6daa3108086497530"
P15_CONTRACT = "implementation/p16/qualification/p15-current-source-v1/contract.json"
P15_CONTRACT_SHA256 = "5391428d584f7be36ed532ea446a07372761fb28bad9446972cef307c35a13e0"
CURRENT_SOURCE_QUALIFIER = "tools/p17/current_workspace_source_qualification.py"

REPLACED_BASE_HASHES = {
    "Cargo.lock": "6561e43d46f89ee42773840dd33747cfa23bd55b0927f1da41e357bf3b97c639",
    "crates/hwpx-package/Cargo.toml": "6d3c404804f313b758223d2f21d400066d9b69e8c5df17e3446f36eb34442a73",
    "tools/p16/postgres_artifact_qualification.py": "0c70221a2a6cf80b26970ea259bb58a0b46dabb3a21398abec43b6e8d619be81",
    "tools/p16/p15_source_qualification.py": "e4c424920bcc040f1f1ea9aaac3e624eb1478866e9d9458dbe75b778bb2cbd5f",
    "tools/p16/tests/test_postgres_artifact_qualification.py": "0cda7bc4d46aa169dfabb4ec55084059ad54d09ce196bd4404d6206b6b90b041",
    "tools/p16/tests/test_p15_source_qualification.py": "76ac1f16b8d0ce831eaaccd0d91f74d6dc601f3d58fc2868a8674761922a1fdd",
}
REPLACED_PATHS = tuple(REPLACED_BASE_HASHES)
REPLACED_SUCCESSOR_HASHES = {
    "Cargo.lock": "7cb6ea91c65c226f2769af0d33906b39970efa0c81b286aa32ca282ef8614d69",
    "crates/hwpx-package/Cargo.toml": "8ad8656643ccfc352aab4a7db1720e8ea2e911aa2837d0d74b73d9349adc392d",
    "tools/p16/postgres_artifact_qualification.py": "dc0099886582bd9a01fdc0693ecc4d58a2617ab7ab78babc4fbc6c8b99b34a4a",
    "tools/p16/p15_source_qualification.py": "6e3ba421f4c0d5f34b8123e918892bf52fca1f11e0263349e8bb59462863bd21",
    "tools/p16/tests/test_postgres_artifact_qualification.py": "a18415a26fd851b9c88512c0db2f8ce761d00ee4d1f30213319c304bd5475430",
    "tools/p16/tests/test_p15_source_qualification.py": "483c22b852742df6a9c55b3f80bb26425b58e70cf9fe16195a01f3479886160b",
}
GUARD_PATHS = (
    "tools/p16/integrated_source_qualification.py",
    "tools/p16/tests/test_integrated_source_qualification.py",
    "implementation/p16/P16-06_MAIN_INTEGRATION_QUALIFICATION.md",
)
GUARD_HASHES = {
    "tools/p16/integrated_source_qualification.py": "43fc5f526597d08eecac720674ed0c3cb039d146dd28c48c62ecf62c16b1f775",
    "tools/p16/tests/test_integrated_source_qualification.py": "9ad0c151c7d63bb5067395463522946d86bf656da8d3805623155c4df054a397",
    "implementation/p16/P16-06_MAIN_INTEGRATION_QUALIFICATION.md": "62b575291c91b3e7ad59b4bf8b670db6ae52a788b2d863b507fd4f3d9362e725",
}
CONTEXT_REVISIONS = {
    "p14_cancel": "8d03bb6b4fb69e73f8921aa26484b400dadf941b",
    "p15_artifact": "dde79ff3fa86953c7f3e6e8e2402479eddee813e",
    "p15_async": "4c6224f6001c5daadaaaec907c0bba86db7c6c0f",
    "p15_auth": "8ac8d74a0f7795315d2dc2e0573f6b9a3a4e11e9",
    "p15_error": "f36a07e988558b4481c50955a0f76bd69c516d9d",
    "p15_handler": "9e7ed73524be0049292fbdf45f2170df6f997fae",
    "p15_inspector": "7ea2f84c244fe5bbd7926ba3f176dc5acafcf624",
    "p15_quota": "e15921a59d45056c46b8ae94b6f6af778746c534",
    "p15_telemetry": "9f9c6932518175906842a2cbb5915a0fb96d0d49",
    "p16_widget": "19d1cf775e5702e1150e35624bf616f1dbf9a34c",
}


class QualificationError(ValueError):
    """Closed qualification failure without source or path data in the message."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_module(name: str, relative: str) -> Any:
    path = ROOT / relative
    specification = importlib.util.spec_from_file_location(name, path)
    require(specification is not None and specification.loader is not None, "module.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def modules() -> tuple[Any, Any]:
    postgres = load_module(
        "p16_postgres_qualification_for_main_integration",
        "tools/p16/postgres_artifact_qualification.py",
    )
    p15 = load_module(
        "p16_p15_qualification_for_main_integration",
        "tools/p16/p15_source_qualification.py",
    )
    return postgres, p15


def load_current_source_qualifier() -> Any:
    return load_module(
        "p17_current_workspace_source_for_p16_integration",
        CURRENT_SOURCE_QUALIFIER,
    )


def current_source_successors(root: Path) -> dict[str, dict[str, Any]]:
    values = load_current_source_qualifier().verified_successors(
        root,
        history_digest=lambda revision, relative: git_digest(root, revision, relative),
    )
    require(isinstance(values, dict), "current_source.successors")
    return values


def git_digest(root: Path, revision: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    require(completed.returncode == 0 and 0 < len(completed.stdout) <= 4_000_000, "history.source")
    return digest(completed.stdout)


def pinned_contract(postgres: Any, root: Path, relative: str, expected: str) -> dict[str, Any]:
    raw = postgres.read_bounded(root, relative, 128 * 1024)
    require(digest(raw) == expected, "predecessor.digest")
    value = postgres.json_value(raw)
    require(isinstance(value, dict), "predecessor.object")
    return value


def require_qualified_current(
    relative: str,
    expected: str,
    observed: str,
    successors: dict[str, dict[str, Any]],
) -> None:
    if observed == expected:
        return
    entry = successors.get(relative)
    require(
        isinstance(entry, dict)
        and entry.get("current_sha256") == observed
        and isinstance(entry.get("accepted_predecessor_sha256s"), list)
        and expected in entry["accepted_predecessor_sha256s"],
        "source.current",
    )


def replacement_pairs(
    postgres: Any,
    root: Path,
    successors: dict[str, dict[str, Any]],
) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for relative, before in REPLACED_BASE_HASHES.items():
        require(git_digest(root, P16_PARENT, relative) == before, "history.base")
        after = REPLACED_SUCCESSOR_HASHES[relative]
        observed = digest(postgres.read_bounded(root, relative))
        require_qualified_current(relative, after, observed, successors)
        require(before != after, "replacement.unchanged")
        result[relative] = (before, after)
    require(
        git_digest(root, MAIN_PARENT, "crates/hwpx-package/Cargo.toml")
        == result["crates/hwpx-package/Cargo.toml"][1],
        "history.main_manifest",
    )
    return result


def require_current(
    postgres: Any,
    root: Path,
    pairs: dict[str, tuple[str, str]],
    relative: str,
    expected: str,
    successors: dict[str, dict[str, Any]],
) -> None:
    observed = digest(postgres.read_bounded(root, relative))
    if observed == expected or pairs.get(relative) == (expected, observed):
        return
    require_qualified_current(relative, expected, observed, successors)


def validate_postgres_predecessor(
    postgres: Any,
    root: Path,
    pairs: dict[str, tuple[str, str]],
    successors: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    contract = pinned_contract(postgres, root, POSTGRES_CONTRACT, POSTGRES_CONTRACT_SHA256)
    predecessor = contract.get("predecessor")
    require(isinstance(predecessor, dict), "postgres.predecessor")
    require(
        digest(postgres.read_bounded(root, predecessor["path"])) == predecessor["sha256"],
        "postgres.predecessor",
    )
    runtime_entries = contract.get("runtime_sources")
    require(isinstance(runtime_entries, list), "postgres.runtime")
    runtime: dict[str, str] = {}
    for entry in runtime_entries:
        require(isinstance(entry, dict) and set(entry) == {"path", "sha256"}, "postgres.runtime")
        require(entry["path"] not in runtime, "postgres.runtime")
        runtime[entry["path"]] = entry["sha256"]
        require_current(postgres, root, pairs, entry["path"], entry["sha256"], successors)
    evidence = contract.get("evidence")
    require(isinstance(evidence, list) and len(evidence) == 2, "postgres.evidence")
    observed_sources = None
    for entry in evidence:
        raw = postgres.read_bounded(root, entry["path"], 32 * 1024)
        require(digest(raw) == entry["sha256"], "postgres.evidence")
        sources = postgres.validate_receipt(postgres.json_value(raw), entry["run_id"])
        require(sources == runtime, "postgres.evidence_sources")
        require(observed_sources is None or observed_sources == sources, "postgres.evidence_independent")
        observed_sources = sources
    guards = contract.get("guard_sources")
    require(isinstance(guards, list), "postgres.guards")
    for entry in guards:
        require_current(postgres, root, pairs, entry["path"], entry["sha256"], successors)
    audited = contract.get("audited_source_commit")
    replacements = contract.get("replacements")
    require(isinstance(audited, str) and isinstance(replacements, list), "postgres.replacements")
    for entry in replacements:
        require(
            git_digest(root, audited, entry["path"]) == entry["successor_sha256"],
            "postgres.history",
        )
    return contract


def validate_p15_predecessor(
    postgres: Any,
    root: Path,
    pairs: dict[str, tuple[str, str]],
    successors: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    contract = pinned_contract(postgres, root, P15_CONTRACT, P15_CONTRACT_SHA256)
    predecessors = contract.get("predecessors")
    require(isinstance(predecessors, list), "p15.predecessors")
    for entry in predecessors:
        require(
            digest(postgres.read_bounded(root, entry["path"], 128 * 1024)) == entry["sha256"],
            "p15.predecessor",
        )
    contexts = contract.get("contexts")
    require(isinstance(contexts, dict) and set(contexts) == set(CONTEXT_REVISIONS), "p15.contexts")
    for name, entries in contexts.items():
        require(isinstance(entries, list), "p15.context")
        for entry in entries:
            relative = entry["path"]
            before = entry["predecessor_sha256"]
            after = entry["successor_sha256"]
            require(git_digest(root, CONTEXT_REVISIONS[name], relative) == before, "p15.history_before")
            require(git_digest(root, P16_PARENT, relative) == after, "p15.history_after")
            require_current(postgres, root, pairs, relative, after, successors)
    guards = contract.get("guard_sources")
    require(isinstance(guards, list), "p15.guards")
    for entry in guards:
        relative = entry["path"]
        expected = entry["sha256"]
        require(git_digest(root, P16_PARENT, relative) == expected, "p15.guard_history")
        require_current(postgres, root, pairs, relative, expected, successors)
    return contract


def verification_paths(root: Path = ROOT) -> set[str]:
    postgres, _ = modules()
    postgres_contract = pinned_contract(postgres, root, POSTGRES_CONTRACT, POSTGRES_CONTRACT_SHA256)
    p15_contract = pinned_contract(postgres, root, P15_CONTRACT, P15_CONTRACT_SHA256)
    paths = {CONTRACT_PATH, POSTGRES_CONTRACT, P15_CONTRACT, *REPLACED_PATHS, *GUARD_PATHS}
    paths.add(postgres_contract["predecessor"]["path"])
    paths.update(entry["path"] for entry in postgres_contract["runtime_sources"])
    paths.update(entry["path"] for entry in postgres_contract["guard_sources"])
    paths.update(entry["path"] for entry in postgres_contract["evidence"])
    paths.update(entry["path"] for entry in p15_contract["predecessors"])
    paths.update(entry["path"] for entry in p15_contract["guard_sources"])
    for entries in p15_contract["contexts"].values():
        paths.update(entry["path"] for entry in entries)
    current = load_current_source_qualifier()
    paths.update(current.verification_paths(root))
    return paths


def expected_contract(root: Path) -> dict[str, Any]:
    postgres, _ = modules()
    successors = current_source_successors(root)
    pairs = replacement_pairs(postgres, root, successors)
    validate_postgres_predecessor(postgres, root, pairs, successors)
    validate_p15_predecessor(postgres, root, pairs, successors)
    for relative in GUARD_PATHS:
        observed = digest(postgres.read_bounded(root, relative))
        require_qualified_current(relative, GUARD_HASHES[relative], observed, successors)
    return {
        "schema_version": "hwpx-agent.p16-main-integration-source-qualification/v1",
        "qualification_id": "p16.main.9cc1db3.62542b0.v1",
        "scope": "current_pc_merged_source_binding_successor_only",
        "parents": {"main": MAIN_PARENT, "p16": P16_PARENT},
        "predecessors": [
            {"path": POSTGRES_CONTRACT, "sha256": POSTGRES_CONTRACT_SHA256},
            {"path": P15_CONTRACT, "sha256": P15_CONTRACT_SHA256},
        ],
        "replacements": [
            {"path": relative, "predecessor_sha256": before, "successor_sha256": after}
            for relative, (before, after) in pairs.items()
        ],
        "guard_sources": [
            {"path": relative, "sha256": GUARD_HASHES[relative]}
            for relative in GUARD_PATHS
        ],
        "claims": {
            "source_qualification_only": True,
            "actual_integrated_postgres_retested": False,
            "p15_phase_complete": False,
            "p16_phase_complete": False,
            "actual_hangul": False,
            "registered_host": False,
            "production": False,
            "other_pc_or_version": False,
        },
    }


def verified_replacements(root: Path) -> dict[str, tuple[str, str]]:
    try:
        postgres, _ = modules()
        contract = postgres.json_value(postgres.read_bounded(root, CONTRACT_PATH, 128 * 1024))
        expected = expected_contract(root)
        require(postgres.exact(contract, expected), "contract.exact")
        result = {
            entry["path"]: (entry["predecessor_sha256"], entry["successor_sha256"])
            for entry in expected["replacements"]
        }
        successors = current_source_successors(root)
        for relative, entry in successors.items():
            current = entry["current_sha256"]
            if relative in result:
                before, after = result[relative]
                if after in entry["accepted_predecessor_sha256s"]:
                    result[relative] = (before, current)
            else:
                result[relative] = (entry["composition_predecessor_sha256"], current)
        return result
    except (OSError, KeyError, TypeError, RecursionError) as error:
        raise QualificationError("qualification.unavailable") from error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.write:
            expected = expected_contract(ROOT)
            destination = ROOT / CONTRACT_PATH
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write((json.dumps(expected, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        replacements = verified_replacements(ROOT)
    except (QualificationError, OSError, KeyError, TypeError) as error:
        code = str(error) if isinstance(error, QualificationError) else "qualification.unavailable"
        print(json.dumps({"decision": "FAIL", "code": code}, sort_keys=True))
        return 1
    print(json.dumps({
        "decision": "PASS",
        "scope": "merged_source_binding_successor_only",
        "replacements": len(replacements),
        "actual_integrated_postgres_retested": False,
        "phase_complete": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
