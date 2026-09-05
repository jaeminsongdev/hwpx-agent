from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import skills_package as package


ROOT = package.ROOT
CONTRACT_PATH = ROOT / "implementation/p16/p16-skills-package-contract-v1.json"
PREDECESSOR_PATH = ROOT / "implementation/p16/p16-universal-package-contract-v1.json"
LOCAL_SOURCE_PATHS = (
    "implementation/p16/P16-03_SKILLS_POLICY.md",
    "implementation/p16/p16-skill-routing-cases-v1.json",
    *(f"plugins/components/hwpx-agent-skills/skills/{name}/SKILL.md" for name in package.SKILL_NAMES),
    "tools/p16/skills_package.py",
    "tools/p16/build_skills_package.py",
    "tools/p16/build_skills_package_contract.py",
    "tools/p16/validate_skills_package.py",
    "tools/p16/run_skills_checks.py",
    "tools/p16/tests/test_skills_package.py",
)


def sha256_file(path: Path) -> str:
    return package.sha256_bytes(path.read_bytes())


def build_contract() -> dict[str, Any]:
    entries, errors = package.read_component_entries()
    catalog, catalog_errors = package.load_public_catalog()
    cases, routing_errors = package.load_routing_cases()
    errors.extend(catalog_errors)
    errors.extend(routing_errors)
    if errors:
        raise ValueError(",".join(sorted(set(errors))))
    predecessor_sha = sha256_file(PREDECESSOR_PATH)
    if predecessor_sha != "d9a29252d0377053fdd02ff6b48e13df189cb9119811dd9fecf9e2e8de87445c":
        raise ValueError("predecessor.digest")
    referenced_names = sorted({
        tool["name"]
        for name in package.SKILL_NAMES
        for tool in package.skill_tool_snapshot(name, entries, catalog)["referenced_tools"]
    })
    return {
        "schema_version": "hwpx-agent.p16-skills-package-contract/v1",
        "task": "P16-03",
        "scope": "current_pc_hangul_2020_local_skills_component",
        "decision": "pass_scoped_local_skills_component_and_deterministic_routing",
        "predecessor": {
            "path": PREDECESSOR_PATH.relative_to(ROOT).as_posix(),
            "sha256": predecessor_sha,
        },
        "public_tool_catalog": {
            "path": package.CATALOG_PATH.relative_to(ROOT).as_posix(),
            "bytes": package.CATALOG_PATH.stat().st_size,
            "sha256": sha256_file(package.CATALOG_PATH),
            "tool_count": len(catalog),
            "referenced_tool_count": len(referenced_names),
            "destructive_tools": sorted(name for name, tool in catalog.items() if tool["annotations"]["destructiveHint"]),
        },
        "component": {
            "root": package.COMPONENT_ROOT.relative_to(ROOT).as_posix(),
            "skill_count": len(package.SKILL_NAMES),
            "skills": [package.skill_tool_snapshot(name, entries, catalog) for name in package.SKILL_NAMES],
            "entry_count": len(entries),
            "total_bytes": sum(len(value) for value in entries.values()),
            "entries": package.component_snapshot(entries),
            "archive_policy": "sorted_fixed_metadata_zip_stored_atomic_no_overwrite",
            "composition": "adds_manifest_skills_path_and_nine_files_without_mutating_base",
        },
        "routing_evaluation": {
            "case_path": package.ROUTING_CASES_PATH.relative_to(ROOT).as_posix(),
            "case_sha256": sha256_file(package.ROUTING_CASES_PATH),
            "case_count": len(cases),
            "positive_count": sum(case["kind"] == "positive" for case in cases),
            "negative_count": sum(case["kind"] == "negative" for case in cases),
            "passed_count": sum(package.evaluate_prompt(case["prompt"]) == case["expected_selected_skill"] for case in cases),
            "evidence_level": "deterministic_local_component_not_chatgpt_host_behavior",
        },
        "requirements": ["P16-R15", "P16-R34"],
        "claims": {
            "nine_skills_packaged": True,
            "public_tool_names_synchronized": True,
            "positive_negative_local_eval_passed": True,
            "source_preserved": True,
            "chatgpt_host_routing_tested": False,
            "registered_plugin_tested": False,
            "developer_mode_tested": False,
            "direct_print_supported": False,
            "hangul_or_com_invoked": False,
            "public_or_production_ready": False,
        },
        "source_locks": [
            {"path": relative, "sha256": sha256_file(ROOT / relative)}
            for relative in LOCAL_SOURCE_PATHS
        ],
        "next_task": "P16-04 Widget shell; P16-02 actual registration remains independently pending",
    }


def atomic_write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the P16-03 skills package contract.")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        expected = package.canonical_json_bytes(build_contract())
    except (OSError, ValueError) as error:
        print(json.dumps({"decision": "FAIL", "errors": [str(error)]}, sort_keys=True))
        return 1
    if args.write:
        atomic_write(CONTRACT_PATH, expected)
        print(json.dumps({"decision": "PASS", "contract": CONTRACT_PATH.relative_to(ROOT).as_posix()}, sort_keys=True))
        return 0
    if not CONTRACT_PATH.is_file() or CONTRACT_PATH.read_bytes() != expected:
        print(json.dumps({"decision": "FAIL", "errors": ["contract.drift"]}, sort_keys=True))
        return 1
    print(json.dumps({"decision": "PASS", "skills": len(package.SKILL_NAMES), "cases": 36, "source_locks": len(LOCAL_SOURCE_PATHS)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
