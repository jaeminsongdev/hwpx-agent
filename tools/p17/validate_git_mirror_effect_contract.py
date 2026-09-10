"""Validate the bounded P17 exact Git mirror effect component contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "protocol/private/p17-git-mirror-effect-v1.json"
SOURCE = ROOT / "crates/remote-sync-host/src/git_mirror.rs"
TEST = ROOT / "crates/remote-sync-host/tests/git_mirror_effect.rs"
REPORT = ROOT / "implementation/p17/P17-06_GIT_MIRROR_EFFECT_V13.md"


class ContractError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ContractError(code)


def load_unique(path: Path) -> dict[str, Any]:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ContractError("contract.duplicate_key")
            result[key] = value
        return result

    bounded = path.is_file() and 0 < path.stat().st_size <= 32_768
    require(bounded, "contract.file")
    try:
        document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError("contract.parse") from error
    require(isinstance(document, dict), "contract.type")
    return document


def validate(document: dict[str, Any]) -> None:
    require(
        list(document)
        == [
            "schema_version",
            "scope",
            "input",
            "repository_admission",
            "state",
            "plan",
            "publish",
            "recovery",
            "receipt",
            "evidence",
        ],
        "contract.keys",
    )
    require(
        document["schema_version"] == "hwpx-agent.git-mirror-effect/v1",
        "schema",
    )
    require(
        document["input"]["accepts_command_or_ref"] is False,
        "input.command",
    )
    admission = document["repository_admission"]
    require(admission["network_transport"] is False, "network")
    require(admission["repository_hooks"] is False, "hooks")
    require(
        document["state"]["tree_contains_only_state"] is True,
        "state.tree",
    )
    require(document["plan"]["canonical_max_bytes"] == 4096, "plan.bound")
    require(
        document["plan"]["writes_only_unreachable_objects"] is True,
        "plan.effect",
    )
    require(
        document["publish"]["old_oid_compare_and_swap"] is True,
        "publish.cas",
    )
    require(document["publish"]["blind_retry"] is False, "publish.retry")
    require(
        document["recovery"]["observations"] == ["no_effect", "committed", "diverged"],
        "recovery.states",
    )
    evidence = document["evidence"]
    require(
        evidence["actual_disposable_local_bare_git"] is True,
        "evidence.git",
    )
    for claim in (
        "actual_remote_network",
        "actual_postgresql_state_machine",
        "authenticated_host_dispatch",
        "persistent_credential_custody",
        "production",
        "p17_06_complete",
    ):
        require(evidence[claim] is False, f"evidence.{claim}")


def validate_sources(root: Path = ROOT) -> None:
    for path in (SOURCE, TEST, REPORT):
        require(path.is_file() and path.stat().st_size > 0, "source.missing")
    source = SOURCE.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    for token in (
        "GitMirrorEffectObservation",
        "pub fn decode(bytes",
        'OsStr::new("update-ref")',
        'OsStr::new("--verify")',
        'OsStr::new("--quiet")',
        "require_exact_tree",
        'env("GIT_TERMINAL_PROMPT", "0")',
        'env("GIT_NO_REPLACE_OBJECTS", "1")',
        ".env_clear()",
    ):
        require(token in source, f"source.token.{token}")
    safe_process = "Command::new" in source and "shell" not in source.lower()
    require(safe_process, "source.process")
    for token in (
        "canonical_plan_survives_restart",
        "concurrent_ref_change_is_diverged",
        "GitMirrorEffectError::ReferenceConflict",
        "GitMirrorEffectError::PlanRejected",
        "read_branch",
    ):
        require(token in tests, f"test.token.{token}")
    require("component evidence only" in report, "report.scope")
    require("P17-06 remains open" in report, "report.open")


def verify(root: Path = ROOT) -> dict[str, Any]:
    document = load_unique(root / CONTRACT.relative_to(ROOT))
    validate(document)
    validate_sources(root)
    return document


if __name__ == "__main__":
    verified = verify()
    print("P17_GIT_MIRROR_EFFECT_CONTRACT_PASS " f"schema={verified['schema_version']}")
