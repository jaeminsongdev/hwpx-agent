"""Verify the exact current-source successor without rewriting predecessor contracts."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable


def load_acceptance() -> Any:
    path = Path(__file__).resolve().with_name("run_current_workspace_source_checks.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_acceptance", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("acceptance.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


acceptance = load_acceptance()


ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v1-20260906"
QUALIFICATION = ROOT / BASE
RUN_ID = "86a24815db10424993c588a6a448556c"
BASE_COMMIT = "949bcb4dd1376cc580c550ffea9e18d46918a31f"
RECEIPT_SHA256 = "213881e250d42a1e831fb304a97147d99ab537eec522ebc5f4d27ccd0b6c1ee0"
CARGO_METADATA_PROJECTION_SHA256 = (
    "8071ba0ee448f663054c4786cc646ebf2bf49307dc773d71b1e347dbd1b43403"
)
WORKSPACE_MEMBER_COUNT = 23
SUCCESSORS: tuple[dict[str, Any], ...] = (
    {
        "accepted_predecessor_sha256s": [
            "6561e43d46f89ee42773840dd33747cfa23bd55b0927f1da41e357bf3b97c639",
            "7cb6ea91c65c226f2769af0d33906b39970efa0c81b286aa32ca282ef8614d69",
        ],
        "composition_predecessor_sha256": "6561e43d46f89ee42773840dd33747cfa23bd55b0927f1da41e357bf3b97c639",
        "current_sha256": "f578f33ab4d24464883c204cf6f04b8f3a4715d6db7132bbf392175e9c54f7b3",
        "path": "Cargo.lock",
    },
    {
        "accepted_predecessor_sha256s": [
            "f8281c9c13ea981ab8652819f1e3946ea942bca2d952f68b05ee61f3a3179c03"
        ],
        "composition_predecessor_sha256": "f8281c9c13ea981ab8652819f1e3946ea942bca2d952f68b05ee61f3a3179c03",
        "current_sha256": "8d48d90ef0f432236cc89a288bc0803ec9cd228d5b7183a4360f6609f53d7a9e",
        "path": "Cargo.toml",
    },
    {
        "accepted_predecessor_sha256s": [
            "52f583c2b18d33a009db93ef59127d9cf2b13000e9e83db5bef523c748bc33aa"
        ],
        "composition_predecessor_sha256": "52f583c2b18d33a009db93ef59127d9cf2b13000e9e83db5bef523c748bc33aa",
        "current_sha256": "7f44605e82a9b8a290961553fc2993b8d7209003d2c55157258d80f7e36e5cb6",
        "path": "crates/artifact-service/src/store/postgres_repository.rs",
    },
    {
        "accepted_predecessor_sha256s": [
            "2c510c70ceca388d0858f0a0e887b84fcbde64d7b2b24cc266d377ec9fc04f63"
        ],
        "composition_predecessor_sha256": "2c510c70ceca388d0858f0a0e887b84fcbde64d7b2b24cc266d377ec9fc04f63",
        "current_sha256": "bed1fcd842f320c3f8df11a80458df94007e9dd86125421fbcb6e48cdc09ca42",
        "path": "crates/mcp-control-plane/Cargo.toml",
    },
    {
        "accepted_predecessor_sha256s": [
            "92a8fe6aad98619ad106f4d037d4002d1049078a07fc2e3d85fa5e0c4fc661dc"
        ],
        "composition_predecessor_sha256": "92a8fe6aad98619ad106f4d037d4002d1049078a07fc2e3d85fa5e0c4fc661dc",
        "current_sha256": "3d066f53a353552e5c1d66c891c7ca2167b92fd07bcdb84f29737513c14e1864",
        "path": "crates/mcp-control-plane/src/lib.rs",
    },
    {
        "accepted_predecessor_sha256s": [
            "ba4d49cc2326c4fc7f43c71396eccbeaf48fcb2f8cf586b6f5e0f2507fd8c3f9"
        ],
        "composition_predecessor_sha256": "ba4d49cc2326c4fc7f43c71396eccbeaf48fcb2f8cf586b6f5e0f2507fd8c3f9",
        "current_sha256": "034eecd9cb64d7b072a4096d320d7f53ff8cfb86c797a44edabeceb5e745d5f9",
        "path": "pnpm-lock.yaml",
    },
    {
        "accepted_predecessor_sha256s": [
            "43fc5f526597d08eecac720674ed0c3cb039d146dd28c48c62ecf62c16b1f775"
        ],
        "composition_predecessor_sha256": "43fc5f526597d08eecac720674ed0c3cb039d146dd28c48c62ecf62c16b1f775",
        "current_sha256": "e8e122e48d97694af7bc59738e96c886795e16d3c50f90b51af6a682c1836400",
        "path": "tools/p16/integrated_source_qualification.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "6e3ba421f4c0d5f34b8123e918892bf52fca1f11e0263349e8bb59462863bd21",
            "e4c424920bcc040f1f1ea9aaac3e624eb1478866e9d9458dbe75b778bb2cbd5f",
        ],
        "composition_predecessor_sha256": "e4c424920bcc040f1f1ea9aaac3e624eb1478866e9d9458dbe75b778bb2cbd5f",
        "current_sha256": "70b04f9edd7c0d7ef88b09f82ca399663dc7d0aa74d1536ca6876114720a89bc",
        "path": "tools/p16/p15_source_qualification.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "8fa11f1137591c18d8160985687ab1e6f9e27d83495424cb7158fd68cb4a5f3a"
        ],
        "composition_predecessor_sha256": "8fa11f1137591c18d8160985687ab1e6f9e27d83495424cb7158fd68cb4a5f3a",
        "current_sha256": "7ecaa4939b0bacc92d3eb0c6c69e9610069193604d7a9f942314d8f80f3ea332",
        "path": "tools/p16/run_postgres_artifact_checks.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "9ad0c151c7d63bb5067395463522946d86bf656da8d3805623155c4df054a397"
        ],
        "composition_predecessor_sha256": "9ad0c151c7d63bb5067395463522946d86bf656da8d3805623155c4df054a397",
        "current_sha256": "c4e12a506a5bbf6cab74bb27a7eea6737147b8fe878118c7570c270e1ce7bd8e",
        "path": "tools/p16/tests/test_integrated_source_qualification.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "483c22b852742df6a9c55b3f80bb26425b58e70cf9fe16195a01f3479886160b",
            "76ac1f16b8d0ce831eaaccd0d91f74d6dc601f3d58fc2868a8674761922a1fdd",
        ],
        "composition_predecessor_sha256": "76ac1f16b8d0ce831eaaccd0d91f74d6dc601f3d58fc2868a8674761922a1fdd",
        "current_sha256": "ff77693dc9c309f4f44f2ad9c885fb73862eeb87b1f87d3e284cbf5045fcfc2f",
        "path": "tools/p16/tests/test_p15_source_qualification.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "b3067b75185437f712b9a3b8c0d4ea22fe467d6d4936c1a99834c0a63d03d56a"
        ],
        "composition_predecessor_sha256": "b3067b75185437f712b9a3b8c0d4ea22fe467d6d4936c1a99834c0a63d03d56a",
        "current_sha256": "a1cf888bf867637d087abc8dd37640a167949bf2c98f81fb02b68b8a733fbe5c",
        "path": "tools/p16/tests/test_postgres_artifact_checks.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "599197fa02f6f2c9d3ff08efd72db417fcd70becab5544abdf013d4b859d9ded"
        ],
        "composition_predecessor_sha256": "599197fa02f6f2c9d3ff08efd72db417fcd70becab5544abdf013d4b859d9ded",
        "current_sha256": "f0fde73e5e506e5ea46daef3acd1fa265df4719c3d08fdeeb0071c2e44bd25d6",
        "path": "tools/p16/validate_widget_shell_successor.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "d87b6ea4737a76bec765d492a34b21839f791af6d3df12aa62e18ca29197f343"
        ],
        "composition_predecessor_sha256": "d87b6ea4737a76bec765d492a34b21839f791af6d3df12aa62e18ca29197f343",
        "current_sha256": "abcd83a904cf0501e0c466d218a498025e4541ef93a21136fccda8536b754f0e",
        "path": "web/plugin-widget/scripts/build-widget.mjs",
    },
)
CLAIMS = {
    "source_qualification_only": True,
    "p05_diagnostic_dependencies_bound": True,
    "actual_hangul": False,
    "registered_host": False,
    "production": False,
    "other_pc_or_version": False,
    "phase_complete": False,
}
GUARD_SOURCES = (
    "tools/p17/run_current_workspace_source_checks.py",
    "tools/p17/current_workspace_source_qualification.py",
    "tools/p17/tests/test_current_workspace_source_qualification.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V1.md",
)
HEX = re.compile(r"[0-9a-f]{64}\Z")


class QualificationError(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def load_document(path: Path, code: str) -> dict[str, Any]:
    require(path.is_file() and 0 < path.stat().st_size <= 512_000, f"{code}.file")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError(f"{code}.parse") from error
    require(isinstance(value, dict), f"{code}.object")
    require(raw == canonical(value), f"{code}.canonical")
    return value


def git_digest(root: Path, revision: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        check=False,
        capture_output=True,
        timeout=30,
    )
    require(completed.returncode == 0 and 0 < len(completed.stdout) <= 4_000_000, "history.source")
    return hashlib.sha256(completed.stdout).hexdigest()


def source_lock(root: Path, relative: str) -> dict[str, Any]:
    path = acceptance.bounded_file(root, relative)
    return {"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)}


def expected_receipt() -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-check/v1",
        "run_id": RUN_ID,
        "scope": "current_pc_source_binding_successor_only",
        "source_commit": BASE_COMMIT,
        "checks": list(acceptance.CHECKS),
        "check_count": len(acceptance.CHECKS),
        "passed": True,
        "decision": "PASS",
        "predecessor_contract_sha256": acceptance.PINNED_CONTRACTS,
        "successors": list(SUCCESSORS),
        "successor_count": len(SUCCESSORS),
        "cargo_metadata_projection_sha256": CARGO_METADATA_PROJECTION_SHA256,
        "cargo_workspace_member_count": WORKSPACE_MEMBER_COUNT,
        "actual_hangul": False,
        "registered_host": False,
        "production": False,
        "other_pc_or_version": False,
        "phase_complete": False,
    }


def validate_receipt(value: dict[str, Any]) -> None:
    expected = expected_receipt()
    require(set(value) == set(expected), "receipt.fields")
    require(value == expected, "receipt.exact")


def receipt_path(root: Path) -> Path:
    return root / "artifacts/p17/current-workspace-source-runs" / RUN_ID / "receipt.json"


def expected_current(root: Path) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v1",
        "scope": "current_pc_source_binding_successor_only",
        "run_id": RUN_ID,
        "source_commit": BASE_COMMIT,
        "predecessor_contract_sha256": acceptance.PINNED_CONTRACTS,
        "successors": list(SUCCESSORS),
        "cargo_metadata_projection_sha256": CARGO_METADATA_PROJECTION_SHA256,
        "cargo_workspace_member_count": WORKSPACE_MEMBER_COUNT,
        "claims": CLAIMS,
        "receipt": {
            "path": f"artifacts/p17/current-workspace-source-runs/{RUN_ID}/receipt.json",
            "sha256": RECEIPT_SHA256,
        },
    }


def expected_contract(root: Path, current_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v1",
        "qualification_id": "p17.current-workspace-source.v1.20260906",
        "base_commit": BASE_COMMIT,
        "scope": "current_pc_source_binding_successor_only",
        "claims": CLAIMS,
        "predecessors": [
            {"path": relative, "sha256": expected}
            for relative, expected in acceptance.PINNED_CONTRACTS.items()
        ],
        "evidence": {
            "path": f"{BASE}/current-host.json",
            "canonical_sha256": digest(current_path),
            "run_id": RUN_ID,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
    }


def verify(root: Path = ROOT) -> dict[str, Any]:
    directory = root / BASE
    current_path = directory / "current-host.json"
    current = load_document(current_path, "current")
    contract = load_document(directory / "contract.json", "contract")
    require(current == expected_current(root), "current.exact")
    require(contract == expected_contract(root, current_path), "contract.exact")
    return contract


def verified_successors(
    root: Path = ROOT,
    history_digest: Callable[[str, str], str] | None = None,
) -> dict[str, dict[str, Any]]:
    verify(root)
    result: dict[str, dict[str, Any]] = {}
    for entry in SUCCESSORS:
        relative = entry.get("path")
        current = entry.get("current_sha256")
        accepted = entry.get("accepted_predecessor_sha256s")
        composition = entry.get("composition_predecessor_sha256")
        require(
            isinstance(relative, str)
            and relative not in result
            and isinstance(current, str)
            and HEX.fullmatch(current) is not None
            and isinstance(accepted, list)
            and accepted == sorted(set(accepted))
            and all(isinstance(value, str) and HEX.fullmatch(value) is not None for value in accepted)
            and isinstance(composition, str)
            and composition in accepted,
            "successor.shape",
        )
        path = acceptance.bounded_file(root, relative)
        require(digest(path) == current, "successor.current")
        historical = (
            git_digest(root, BASE_COMMIT, relative)
            if history_digest is None
            else history_digest(BASE_COMMIT, relative)
        )
        require(historical == current, "successor.history")
        result[relative] = dict(entry)
    require(result, "successor.empty")
    return result


def verification_paths(root: Path = ROOT) -> set[str]:
    del root
    return {
        f"{BASE}/current-host.json",
        f"{BASE}/contract.json",
        *acceptance.PINNED_CONTRACTS,
        *(entry["path"] for entry in SUCCESSORS),
        *GUARD_SOURCES,
    }


def qualify() -> tuple[Path, Path]:
    receipt = load_document(receipt_path(ROOT), "receipt")
    validate_receipt(receipt)
    require(digest(receipt_path(ROOT)) == RECEIPT_SHA256, "receipt.digest")
    verified_successors_from_receipt = {entry["path"]: entry for entry in receipt["successors"]}
    require(len(verified_successors_from_receipt) == len(SUCCESSORS), "receipt.successors")
    for entry in SUCCESSORS:
        require(verified_successors_from_receipt.get(entry["path"]) == entry, "receipt.successor")
        require(git_digest(ROOT, BASE_COMMIT, entry["path"]) == entry["current_sha256"], "history.source")
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(canonical(expected_current(ROOT)))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: current_workspace_source_qualification.py RUN_ID|verify")
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit("usage: current_workspace_source_qualification.py RUN_ID|verify")
