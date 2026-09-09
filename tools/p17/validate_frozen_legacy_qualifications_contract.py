"""Validate the private contract for frozen legacy source qualifications."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import frozen_current_source_history_v1 as history  # noqa: E402
from tools.p17 import frozen_current_source_v39 as frozen_v39  # noqa: E402
from tools.p17 import frozen_local_qualifications_v1 as local  # noqa: E402
from tools.p17 import frozen_source_successor_pairs_v1 as pairs  # noqa: E402

CONTRACT_RELATIVE = "protocol/private/p17-frozen-legacy-qualifications-v1.json"
CURRENT_WORKSPACE_TESTS = (
    "tools/p17/tests/test_current_workspace_source_qualification.py",
    *(
        f"tools/p17/tests/test_current_workspace_source_qualification_v{version}.py"
        for version in range(21, 39)
    ),
)
MIGRATED_TESTS = (
    *CURRENT_WORKSPACE_TESTS,
    "tools/p17/tests/test_frozen_current_source_history_v1.py",
    "tools/p17/tests/test_frozen_current_source_v12.py",
    "tools/p17/tests/test_frozen_local_qualifications_v1.py",
    "tools/p17/tests/test_frozen_p15_source_v1.py",
    "tools/p17/tests/test_frozen_source_successor_pairs_v1.py",
    "tools/p17/tests/test_local_daemon_qualification.py",
    "tools/p17/tests/test_local_mcp_plugin_qualification.py",
    "tools/p17/tests/test_main_bound_plugin_qualification.py",
    "tools/p17/tests/test_postgres_checkpoint_host_qualification.py",
    "tools/p17/tests/test_telemetry_source_successor_bridge.py",
    "tools/p17/tests/test_widget_plugin_prepare_qualification.py",
)
SOURCE_PATHS = tuple(
    sorted(
        (
            "implementation/p17/P17_FROZEN_LEGACY_SOURCE_QUALIFICATIONS.md",
            "protocol/migrations/"
            "p17-legacy-mutable-source-qualifications-to-frozen-v1.md",
            "tools/p17/frozen_current_source_history_v1.py",
            "tools/p17/frozen_local_qualifications_v1.py",
            "tools/p17/frozen_source_successor_pairs_v1.py",
            *MIGRATED_TESTS,
            "tools/p17/tests/test_frozen_legacy_qualifications_contract.py",
            "tools/p17/validate_frozen_legacy_qualifications_contract.py",
        )
    )
)
EXPECTED_COVERAGE = {
    "current_workspace_first_version": 20,
    "current_workspace_last_version": 39,
    "current_workspace_qualification_count": 20,
    "local_qualification_count": 5,
    "local_runtime_source_count": 86,
    "local_guard_source_count": 18,
    "v12_source_count": 121,
    "p15_context_count": 10,
    "initial_p17_test_count": 178,
    "initial_error_count": 31,
    "current_p17_test_count": 199,
    "current_error_count": 0,
}
EXPECTED_INVARIANTS = [
    "bounded_git_reads",
    "exact_contract_current_and_source_blobs",
    "fixed_full_commit_ancestry",
    "legacy_generators_preserved",
    "no_current_worktree_source_authority",
    "no_receipt_blob_promotion",
    "no_skipped_or_weakened_tests",
]
EXPECTED_CLAIMS = {
    "actual_hangul": False,
    "historical_source_state_verified": True,
    "other_pc_or_version": False,
    "p17_phase_complete": False,
    "product_complete": False,
    "production": False,
    "receipt_blobs_verified": False,
    "registered_host": False,
    "remote_pull_or_push": False,
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenLegacyContractError(ValueError):
    """Fail-closed private-contract validation error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenLegacyContractError(code)


def unique_object(pairs_value: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs_value:
        require(key not in result, "contract.duplicate")
        result[key] = value
    return result


def bounded_file(root: Path, relative: str, maximum: int = 4_000_000) -> Path:
    try:
        frozen_v39.validate_relative_path(relative)
    except frozen_v39.FrozenSourceV39Error as error:
        raise FrozenLegacyContractError("source.path") from error
    require(type(maximum) is int and 0 < maximum <= 4_000_000, "source.limit")
    resolved_root = root.resolve(strict=True)
    cursor = resolved_root
    for part in relative.split("/"):
        cursor /= part
        require(
            not cursor.is_symlink()
            and not (hasattr(cursor, "is_junction") and cursor.is_junction()),
            "source.link",
        )
    try:
        resolved = cursor.resolve(strict=True)
    except OSError as error:
        raise FrozenLegacyContractError("source.file") from error
    require(
        resolved_root in resolved.parents
        and resolved.is_file()
        and 0 < resolved.stat().st_size <= maximum,
        "source.file",
    )
    return resolved


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_contract(root: Path = ROOT) -> dict[str, Any]:
    raw = bounded_file(root, CONTRACT_RELATIVE, 512_000).read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrozenLegacyContractError("contract.json") from error
    require(isinstance(value, dict), "contract.object")
    return value


def validate_document(root: Path, contract: dict[str, Any]) -> None:
    require(
        set(contract)
        == {
            "schema_version",
            "contract_id",
            "scope",
            "coverage",
            "invariants",
            "claims",
            "source_locks",
        },
        "contract.shape",
    )
    require(
        contract.get("schema_version")
        == "hwpx-agent.p17-frozen-legacy-qualifications/v1"
        and contract.get("contract_id") == "p17.frozen-legacy-qualifications.v1"
        and contract.get("scope")
        == "immutable_historical_source_qualification_verification",
        "contract.identity",
    )
    require(contract.get("coverage") == EXPECTED_COVERAGE, "contract.coverage")
    require(contract.get("invariants") == EXPECTED_INVARIANTS, "contract.invariants")
    require(contract.get("claims") == EXPECTED_CLAIMS, "contract.claims")
    locks = contract.get("source_locks")
    if not isinstance(locks, list):
        raise FrozenLegacyContractError("source.count")
    require(len(locks) == len(SOURCE_PATHS), "source.count")
    observed_paths: list[str] = []
    for entry in locks:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "bytes", "sha256"},
            "source.shape",
        )
        relative = entry.get("path")
        expected_bytes = entry.get("bytes")
        expected_sha256 = entry.get("sha256")
        if not isinstance(relative, str):
            raise FrozenLegacyContractError("source.identity")
        require(
            relative not in observed_paths
            and type(expected_bytes) is int
            and 0 < expected_bytes <= 4_000_000
            and isinstance(expected_sha256, str)
            and HEX64.fullmatch(expected_sha256) is not None,
            "source.identity",
        )
        path = bounded_file(root, relative)
        require(path.stat().st_size == expected_bytes, "source.bytes")
        require(digest(path) == expected_sha256, "source.digest")
        observed_paths.append(relative)
    require(tuple(observed_paths) == SOURCE_PATHS, "source.paths")


def verify(root: Path = ROOT) -> dict[str, Any]:
    contract = load_contract(root)
    validate_document(root, contract)
    v20 = history.verify_version(root, 20)
    v39 = history.verify_version(root, 39)
    require(
        v20.get("qualification_id") == history.qualification_id(20)
        and v39.get("qualification_id") == history.qualification_id(39)
        and len(history.verified_implementation_sources(root, 20)) == 118
        and len(history.verified_successors(root, 20)) == 25
        and len(history.verified_implementation_sources(root, 39)) == 7
        and len(history.verified_successors(root, 39)) == 26,
        "history.current_workspace",
    )
    runtime_count = 0
    guard_count = 0
    for name in local.QUALIFICATIONS:
        local.verify(name, root)
        sources = local.verified_sources(name, root)
        runtime_count += len(sources["runtime_sources"])
        guard_count += len(sources["guard_sources"])
    require(runtime_count == 86 and guard_count == 18, "history.local")
    require(len(pairs.v12_source_hashes(root)) == 121, "history.v12")
    p15 = pairs.locked_json(
        root,
        pairs.P15_CONTRACT_RELATIVE,
        pairs.P15_CONTRACT_BYTES,
        pairs.P15_CONTRACT_SHA256,
        "p15.contract",
    )
    require(
        isinstance(p15.get("contexts"), dict)
        and len(p15["contexts"]) == 10
        and p15.get("claims") == pairs.P15_EXPECTED_CLAIMS,
        "history.p15",
    )
    return contract


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit(
            "usage: validate_frozen_legacy_qualifications_contract.py verify"
        )
    try:
        verified = verify()
    except (
        FrozenLegacyContractError,
        frozen_v39.FrozenSourceV39Error,
        history.FrozenSourceHistoryError,
        local.FrozenLocalQualificationError,
        pairs.FrozenSuccessorPairError,
    ) as error:
        print(f"P17_FROZEN_LEGACY_CONTRACT_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(
        "P17_FROZEN_LEGACY_CONTRACT_PASS "
        f"contract={verified['contract_id']} sources={len(verified['source_locks'])}"
    )
