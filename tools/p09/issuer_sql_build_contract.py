"""Explicit legacy/current probe receipts; never restamp build-only into SQL/Gate PASS.

현재 r4의 immutable receipt와 helper/source/보호 EXE 전부를 paced reader로
fresh 결합한다. 기존 drivers의 SQL/보안/원본 범위 및 종료 final hash는 유지한다.
"""
from pathlib import Path
import re

import conservative_maintenance as c
import build_current_issuer_probe as current
import current_issuer_build_inputs as inputs
import owned_probe_build as compiler
from sql_runtime_supervision import SOURCES as RUNTIME_SOURCES

CURRENT_BUILD_PIN = {"path": "target/p09-149-current-issuer-build/current-issuer-build-r4.json",
    "bytes": 305455, "sha256": "5ce53cf4938ceaa2e8295644e57e3f4fc8becc6a20bdaca4db9cfb6bf5be86c7"}
ARCHIVE = "implementation/p09/source-archive/p09-149-pre-current-sql-build-contract/source-preimages.v1.json"
SOURCES = ["tools/p09/issuer_sql_build_contract.py", "tools/p09/tests/test_issuer_sql_build_contract.py",
    "tools/p09/tests/sql_build_driver_delta.py", "tools/p09/verify_issuer_sql_build_contract.py", ARCHIVE,
    "implementation/p09/source-archive/p09-149-pre-sql-build-contract-guard-compatibility/source-preimages.v1.json",
    "implementation/p09/evidence/p09-149-current-SQL-build-contract.light-source-run01.v1.json"]+RUNTIME_SOURCES


def direct_name(path):
    source = c.ROOT/path
    c.require(source.is_absolute() and source.is_relative_to(c.ROOT)
        and all(part not in ("", ".", "..") for part in source.relative_to(c.ROOT).parts), "SQL_BUILD_PATH_SCOPE")
    for item in (source, *source.parents):
        if item == c.ROOT.parent:
            break
        c.require(not item.is_symlink() and not item.is_junction(), "SQL_BUILD_PATH_LINK")
    return source.relative_to(c.ROOT).as_posix()


def build_contract(build, scheme):
    # Preserve every original accepted-build guard for both receipt generations.
    c.require(build["exit_code"] == 0 and build["source_freeze_exact_after"]
        and build["protected_executables_exact_after"] and build["logical_cpu_limit"] == build["cargo_jobs"] == 1
        and build["priority"] == "BelowNormal" and not build["diagnostics"]
        and build["catalog_profile"]["test"] is False, "accepted_probe_build_missing")
    c.require(build["whole_workspace_Rust_input_coverage_enforced"] and build["historical_parent_archive_verified"]
        and len(build["source_freeze"]) == 842 and len(build["protected_executables"]) >= 37,
        "new_build_coverage_missing")
    sources = inputs.inventory(build["source_freeze"], 842)
    protected = inputs.inventory(build["protected_executables"])
    if scheme == "legacy":
        c.require(build["state"] == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE", "accepted_probe_build_missing")
        helpers = {}
        target = inputs.LEGACY
    else:
        c.require(scheme == "current_r4" and build["state"] == current.PASS
            and build.get("variant") == "r4" and build.get("compiler_build_binding_accepted") is True
            and build.get("build_helper_freeze_exact_after") is True and build.get("mutex_cleanup_confirmed") is True
            and current.build_accepted(build) and len(protected) == 50, "SQL_BUILD_CURRENT_NOT_ACCEPTED")
        c.require(build.get("product_complete") is False and build.get("P09_gate") == "OPEN"
            and build.get("actual_SQL_or_native_product_executed") is False
            and build.get("baseline_candidate_pin") == current.CANDIDATE_PIN, "SQL_BUILD_CURRENT_PHASE_SCOPE")
        helpers = inputs.inventory(build["build_helper_freeze"], 29)
        expected = set(compiler.SOURCES+["tools/p09/tests/test_owned_sql_job.py"]+inputs.EXTRA
            +current.OWN_SOURCES+[current.CANDIDATE_PIN["path"], "rust-toolchain.toml"])
        c.require(set(helpers) == expected, "SQL_BUILD_CURRENT_HELPER_CLOSURE")
        target = inputs.CURRENT_TARGET
    executable = inputs.pin_shape(build["executable_pin"])
    c.require(re.fullmatch(re.escape(target)+r"/debug/examples/formula_issuer_product_postgres_probe-p143-r[1-9][0-9]*\.exe",
        executable["path"]) is not None and executable["path"] not in protected, "crypto_executable_binding_drift")
    return sources, protected, helpers, executable


def bind_probe_build(reader, build_file):
    name = direct_name(build_file)
    if name == CURRENT_BUILD_PIN["path"]:
        scheme = "current_r4"
        c.require(reader.pin(name) == CURRENT_BUILD_PIN, "SQL_BUILD_CURRENT_RECEIPT_DRIFT")
    else:
        scheme = "legacy"
        c.require((c.ROOT/name).is_relative_to(c.ROOT/inputs.LEGACY)
            and Path(name).suffix == ".json", "build_receipt_outside_target")
    build = reader.json(name)
    sources, protected, helpers, executable = build_contract(build, scheme)
    # The original driver checks these again, and reader.finish hashes all bound
    # inputs afresh. Never cache away an original repeated pin or final read.
    for pin in [*sources.values(), *protected.values(), *helpers.values(), executable]:
        c.require(reader.pin(direct_name(pin["path"])) == pin, "SQL_BUILD_INPUT_DRIFT")
    binding = {"scheme": scheme, "build_state": build["state"], "receipt_pin": reader.pin(name),
        "build_helper_pins": list(helpers.values()), "actual_SQL_qualified": False}
    return build, executable, binding


def consumer_sources(binding):
    c.require(binding.get("scheme") in {"legacy", "current_r4"}
        and binding.get("actual_SQL_qualified") is False, "SQL_BUILD_CONSUMER_PHASE_SCOPE")
    return SOURCES+[pin["path"] for pin in binding["build_helper_pins"]]
