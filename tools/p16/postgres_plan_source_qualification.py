"""Validate the immutable P16 PostgreSQL plan-source v11 successor evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p16/qualification/plan-source-v11-20260906-v1"
RECEIPT_PATH = f"{BASE}/current-db.json"
CONTRACT_PATH = f"{BASE}/contract.json"
BASE_COMMIT = "5166fe5a684415534af920d55b06043168302d37"
IMAGE = "postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568"
RUN_ID = "b4ad5c050f0d42509da56f072ba5d6fa"
HEX = re.compile(r"[0-9a-f]{64}\Z")
MAX_BYTES = 512 * 1024
REQUIRED_CHECKS = (
    "synthetic_identity_derived_by_product_code", "all_eleven_migrations_applied",
    "guarded_empty_v11_rollback_reapply", "service_revision_receipt_and_graph_binding_seeded",
    "binding_creator_mismatch", "rust_verify", "rust_expect-stale", "restart_owned_loopback_endpoint_revalidated",
    "rust_verify", "postgres_restart_preserves_authoritative_source", "rust_expect-not-found",
    "rust_expect-not-found", "cross_tenant_rls", "rust_expect-source-unavailable", "rust_verify",
    "rust_expect-not-found", "rust_expect-not-found", "rust_verify", "bypass_rls_role_rejected",
    "replication_role_rejected",
    "rust_reject-policies", "rust_reject-policies", "rust_reject-privileges",
    "rust_reject-privileges", "rust_reject-policies", "rust_reject-migrations", "binding_immutable",
    "nonempty_rollback_rejected", "rust_verify",
)
GUARD_PATHS = (
    "tools/p16/postgres_plan_source_qualification.py",
    "tools/p16/tests/test_postgres_plan_source_qualification.py",
    "implementation/p16/P16-06_POSTGRES_PLAN_SOURCE_V11.md",
)


class QualificationError(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def read_bounded(root: Path, relative: str, maximum: int = MAX_BYTES) -> bytes:
    require(isinstance(relative, str) and 0 < len(relative) <= 240, "path.shape")
    require("\\" not in relative and ":" not in relative and "\0" not in relative, "path.syntax")
    require(not PurePosixPath(relative).is_absolute()
            and all(part not in ("", ".", "..") for part in relative.split("/")), "path.escape")
    base = root.resolve(strict=True)
    cursor = base
    for part in relative.split("/"):
        cursor /= part
        require(not cursor.is_symlink()
                and not (hasattr(cursor, "is_junction") and cursor.is_junction()), "path.link")
    path = cursor.resolve(strict=True)
    require(base in path.parents and path.is_file() and 0 < path.stat().st_size <= maximum,
            "path.file")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    require(0 < len(raw) <= maximum, "file.bound")
    return raw


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_json(raw: bytes) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            require(key not in result, "json.duplicate")
            result[key] = value
        return result
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(QualificationError("json.constant")))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise QualificationError("json.invalid") from error


def validate_receipt(root: Path) -> tuple[dict[str, str], str]:
    raw = read_bounded(root, RECEIPT_PATH)
    value = load_json(raw)
    require(isinstance(value, dict), "receipt.object")
    fixed = {
        "actual_hangul": False, "actual_renderer": False, "decision": "PASS",
        "durable_plan_store": False, "failed_stage": None, "failure": None, "image": IMAGE,
        "owned_resources_removed": True, "registered_host": False, "run_id": RUN_ID,
        "schema_version": "hwpx-agent.p16-postgres-plan-source-acceptance/v1",
        "scope": "current_pc_disposable_postgres_plan_source_only",
    }
    require(set(value) == set(fixed) | {"checks", "probe_sha256", "source_sha256"}, "receipt.keys")
    require(all(type(value[key]) is type(wanted) and value[key] == wanted
                for key, wanted in fixed.items()), "receipt.state")
    require(value["checks"] == list(REQUIRED_CHECKS), "receipt.checks")
    require(isinstance(value["probe_sha256"], str)
            and HEX.fullmatch(value["probe_sha256"]) is not None, "receipt.probe")
    sources = value["source_sha256"]
    require(isinstance(sources, dict) and sources, "receipt.sources")
    require(all(isinstance(path, str) and isinstance(value, str) and HEX.fullmatch(value)
                for path, value in sources.items()), "receipt.source_shape")
    for relative, expected in sources.items():
        require(digest(read_bounded(root, relative)) == expected, "source.digest")
    canonical = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return sources, digest(canonical)


def expected_contract(root: Path) -> dict[str, Any]:
    sources, receipt_digest = validate_receipt(root)
    return {
        "schema_version": "hwpx-agent.p16-postgres-plan-source-qualification/v1",
        "qualification_id": "p16.plan-source.v11.20260906.v1", "base_commit": BASE_COMMIT,
        "scope": "current_pc_authoritative_plan_source_successor_only",
        "evidence": {"path": RECEIPT_PATH, "canonical_sha256": receipt_digest, "run_id": RUN_ID},
        "runtime_sources": [{"path": path, "sha256": sources[path]} for path in sorted(sources)],
        "guard_sources": [{"path": path, "sha256": digest(read_bounded(root, path))}
                          for path in GUARD_PATHS],
        "claims": {"authoritative_plan_source": True, "postgres_restart": True,
                   "durable_plan_store": False, "actual_renderer": False, "actual_hangul": False,
                   "registered_host": False, "production": False, "phase_complete": False},
    }


def verify(root: Path = ROOT) -> dict[str, Any]:
    expected = expected_contract(root)
    observed = load_json(read_bounded(root, CONTRACT_PATH))
    require(observed == expected, "contract.exact")
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.write:
            destination = ROOT / CONTRACT_PATH
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write((json.dumps(expected_contract(ROOT), indent=2, sort_keys=True) + "\n").encode("utf-8"))
        contract = verify(ROOT)
    except (QualificationError, OSError, KeyError, TypeError) as error:
        code = str(error) if isinstance(error, QualificationError) else "qualification.unavailable"
        print(json.dumps({"decision": "FAIL", "code": code}, sort_keys=True))
        return 1
    print(json.dumps({"decision": "PASS", "runtime_sources": len(contract["runtime_sources"]),
                      "phase_complete": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
