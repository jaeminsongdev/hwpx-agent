"""P149 current issuer build-input contract; paced, read-only, never starts Cargo.

역사적 build/EXE의 pin을 바꾸지 않는다. 명시된 Rust9와 supervised PS delta만
현재 입력 후보에 인정하며, 제품 의미/실제 compiler/SQL/Gate qualification은 별도다.
"""
import argparse
import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import time

import conservative_maintenance as c
from audit_evidence_io import AuditEvidenceReader, CHUNK_BYTES, MAX_PARSE_BYTES, READ_BYTES_PER_SECOND
from owned_probe_build import MUTEX
from sql_percentage_resources import PercentageResources

LEGACY = "target/p09-121-resource-optimized"
CURRENT_TARGET = "target/p09-149-current-issuer-build"
BASELINE = LEGACY+"/p143-issuer-product-build-r14.json"
HISTORICAL = LEGACY+"/p139-provision-build-r7.json"
DRIFT_AUDIT = "implementation/p09/evidence/p09-149-live-SQL-build-binding.run01.v1.json"
SUPERVISOR = "implementation/p09/evidence/p09-149-owned-probe-build.light-source-progress-run02.v1.json"
BUILDER = "tools/p09/build_formula_issuer_product_probe.ps1"
PARENT = "crates/artifact-service/src/store/postgres_repository.rs"
PARENT_ARCHIVE = "implementation/p09/source-archive/p09-142-pre-artifact-schema22/source-preimages.v1.json"
RUST_CHANGES = frozenset({"crates/domain-ir/src/document_graph.rs", "crates/domain-ir/tests/document_graph.rs",
    "crates/hwpx-package/src/document_import/fields/semantics/evaluation/source.rs",
    "crates/hwpx-package/src/document_import/structure/review/locations.rs",
    "crates/product-cli/src/comment_operation/rich_bodies.rs", "crates/product-cli/src/comment_operation.rs",
    "crates/product-cli/src/form_stored_provider/comments/rich_bodies.rs",
    "crates/product-cli/src/form_stored_provider/comments.rs",
    "crates/product-cli/src/form_value_operation/full_document.rs"})
EXTRA = ["tools/p09/current_issuer_build_inputs.py", "tools/p09/tests/test_current_issuer_build_inputs.py",
    "tools/p09/verify_current_issuer_build_inputs_light.py",
    "implementation/p09/source-archive/p09-149-pre-current-build-parent-archive-repair/source-preimages.v1.json",
    "implementation/p09/evidence/p09-149-current-issuer-build-inputs.run01.v1.json"]


def require(ok, code):
    c.require(ok, "CURRENT_ISSUER_"+code)


def pin_shape(pin):
    require(isinstance(pin, dict) and set(pin) == {"path", "bytes", "sha256"}, "PIN_SHAPE")
    name = pin["path"]
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name
        and not name.startswith("/") and all(part not in ("", ".", "..") for part in name.split("/")), "PIN_PATH")
    require(type(pin["bytes"]) is int and 0 <= pin["bytes"] <= 1024**3
        and isinstance(pin["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]), "PIN_VALUE")
    return pin


def inventory(rows, count=None):
    require(isinstance(rows, list) and 1 <= len(rows) <= 2048 and (count is None or len(rows) == count), "INVENTORY_COUNT")
    pins = [pin_shape(row) for row in rows]
    require(len({row["path"] for row in pins}) == len(pins), "INVENTORY_DUPLICATE")
    return {row["path"]: row for row in pins}


def baseline_contract(build):
    require(build.get("state") == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE" and type(build.get("exit_code")) is int
        and build["exit_code"] == 0 and build.get("source_freeze_exact_after") is True
        and build.get("protected_executables_exact_after") is True
        and build.get("whole_workspace_Rust_input_coverage_enforced") is True
        and build.get("historical_parent_archive_verified") is True and build.get("build_finished_success") is True
        and not build.get("diagnostics") and (build.get("catalog_profile") or {}).get("test") is False,
        "BASELINE_NOT_ACCEPTED")
    require(type(build.get("logical_cpu_limit")) is int and build["logical_cpu_limit"] == 1
        and type(build.get("cargo_jobs")) is int and build["cargo_jobs"] == 1
        and build.get("priority") == "BelowNormal", "BASELINE_RESOURCE_CONTRACT")
    source = inventory(build["source_freeze"], 842)
    protected = inventory(build["protected_executables"]+[pin_shape(build["executable_pin"])], 50)
    require(len(build["protected_executables"]) == 49 and build["executable_pin"]["path"] ==
        LEGACY+"/debug/examples/formula_issuer_product_postgres_probe-p143-r14.exe", "BASELINE_EXECUTABLE_SCOPE")
    return source, protected


def reviewed_deltas(audit, qualification):
    require(audit.get("state") == "INPUT_CHANGED_REBUILD_REQUIRED_NOT_SQL_OR_GATE"
        and audit.get("source_drift_count") == 9 and audit.get("protected_drift_count") == 0
        and audit.get("missing_or_link_count") == 0 and audit.get("source_checked") == 842
        and audit.get("protected_checked") == 50 and audit.get("observed_inputs_fresh_after") is True
        and audit.get("helper_freeze_exact_after") is True and audit.get("compiler_build_binding_accepted") is False
        and set(audit.get("public_code_drift_paths", [])) == RUST_CHANGES, "RUST_DELTA_EVIDENCE")
    audit_pins = inventory(audit["helper_freeze"], 51)
    require(RUST_CHANGES.issubset(audit_pins), "RUST_DELTA_PINS_MISSING")
    require(qualification.get("state") == "PASS_COMPILER_SUPERVISOR_SOURCE_MOCK_ONLY_NOT_BUILD_SQL_OR_GATE"
        and qualification.get("tests_run") == qualification.get("tests_passed") == 23
        and not qualification.get("failed_tests") and qualification.get("source_freeze_exact_after") is True
        and qualification.get("actual_Cargo_Rustc_SQL_Docker_native_child_or_full_audit_run") is False,
        "BUILDER_DELTA_EVIDENCE")
    helper_pins = inventory(qualification["source_freeze"], 14)
    require(BUILDER in helper_pins, "BUILDER_DELTA_PIN_MISSING")
    approved = {name: audit_pins[name] for name in sorted(RUST_CHANGES)}
    approved[BUILDER] = helper_pins[BUILDER]
    return approved, helper_pins


class BuildInputReader(AuditEvidenceReader):
    def _source(self, name):
        pin_shape({"path": name, "bytes": 0, "sha256": "0"*64})
        source = super()._source(name)
        require(source.resolve().is_relative_to(self.root.resolve()), "INPUT_OUTSIDE_ROOT")
        for parent in source.parents:
            require(not parent.is_symlink() and not parent.is_junction(), "INPUT_PARENT_LINK")
            if parent == self.root:
                break
        return source


def bind_current_sources(reader, baseline, approved):
    require(set(approved) == RUST_CHANGES|{BUILDER} and set(approved).issubset(baseline), "DELTA_ALLOWLIST_SCOPE")
    current, changed = [], []
    for name, old in baseline.items():
        actual = reader.fresh_pin(name)
        require(actual == approved.get(name, old), "UNREVIEWED_SOURCE_DRIFT")
        current.append(actual)
        if actual != old:
            changed.append(name)
    require(set(changed) == set(approved), "DECLARED_DELTA_NOT_EXACT")
    return current, sorted(changed)


def verify_historical_parent(reader, old):
    archive = reader.json(PARENT_ARCHIVE)
    rows = [row for row in archive["files"] if row["path"] == PARENT]
    require(len(rows) == 1 and PARENT in old, "PARENT_PREIMAGE_MISSING")
    row = rows[0]
    require(set(row) in ({"path", "base64_chunks"}, {"path", "bytes", "sha256", "base64_chunks"}), "PARENT_ARCHIVE_ROW_SCOPE")
    raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
    digest = hashlib.sha256(raw).hexdigest()
    require(len(raw) == old[PARENT]["bytes"] and digest == old[PARENT]["sha256"], "PARENT_PREIMAGE_DRIFT")
    if "bytes" in row:
        require(len(raw) == row["bytes"] and digest == row["sha256"], "PARENT_PREIMAGE_DRIFT")
    original = raw.decode("utf-8").replace("\r\n", "\n")
    marker = "pub mod source_formula_policy;\n"
    require(original.count(marker) == 1, "PARENT_MODULE_INSERTION_SCOPE")
    expected = original.replace(marker, marker+"pub mod schema22;\n")
    require(reader.text(PARENT) == expected, "PARENT_UNDECLARED_CHANGE")


def historical_receipts(root):
    names = []
    directory = root/LEGACY
    for pattern in ("p142-root-crypto-build-r*.json", "p143-issuer-product-build-r*.json"):
        matches = sorted(directory.glob(pattern))
        require(len(matches) <= 128, "HISTORY_RECEIPT_BUDGET")
        names.extend(path.relative_to(root).as_posix() for path in matches)
    return names


def protected_closure(reader, history_names):
    provision = reader.json("implementation/p09/evidence/p09-139-formula-issuer-registry-provision.source-progress.v1.json")
    reads = reader.json("implementation/p09/evidence/p09-137-formula-issuer-registry-reads.source-progress.v1.json")
    management = reader.json("implementation/p09/evidence/p09-138-formula-issuer-registry-management.source-progress.v1.json")
    rows = list(reader.json(LEGACY+"/p135-case-001-attempt-001.json")["protected_executables"])
    rows += reads["current_executables"]+reads["earlier_executables_preserved"]+[management["current_executable"]]
    rows += [provision["current_executable"]]+provision["earlier_executables_preserved"]
    for number in (2, 3, 4, 5):
        rows.append(reader.json(LEGACY+f"/p141-adapter-build-r{number}.json")["executable_pin"])
    partial = reader.json("implementation/p09/evidence/p09-142-artifact-schema22.implementation-progress.v1.json")
    rows.append(partial["unit_runtime"]["executable_pin"])
    for name in history_names:
        receipt = reader.json(name)
        if receipt["state"] != "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE":
            continue
        pin = pin_shape(receipt["executable_pin"])
        pattern = r"target/p09-121-resource-optimized/debug/examples/" + (
            r"formula_registry_crypto_postgres_probe-p142-r[1-9][0-9]*\.exe" if "p142-root-crypto" in name
            else r"formula_issuer_product_postgres_probe-p143-r[1-9][0-9]*\.exe")
        require(re.fullmatch(pattern, pin["path"]), "HISTORY_EXECUTABLE_SCOPE")
        rows.append(pin)
    return inventory(rows, 50)


def rust_inputs(root, checkpoint):
    names = set()
    for relative in ("crates", "protocol/generated/rust", "tools/xtask"):
        require((root/relative).is_dir(), "RUST_INPUT_DIRECTORY_MISSING")
        for directory, dirs, files in os.walk(root/relative, followlinks=False):
            checkpoint()
            parent = Path(directory)
            require(not parent.is_symlink() and not parent.is_junction(), "RUST_INPUT_DIRECTORY_LINK")
            for name in dirs:
                child = parent/name
                require(not child.is_symlink() and not child.is_junction(), "RUST_INPUT_DIRECTORY_LINK")
            for name in files:
                if name.endswith(".rs") or name == "Cargo.toml":
                    child = parent/name
                    require(child.is_file() and not child.is_symlink() and not child.is_junction(), "RUST_INPUT_FILE_LINK")
                    names.add(child.relative_to(root).as_posix())
                    require(len(names) <= 2048, "RUST_INPUT_INVENTORY_BUDGET")
    return names


def target_contract(root):
    target = root/CURRENT_TARGET
    for directory in (root, root/"target"):
        require(directory.is_dir() and not directory.is_symlink() and not directory.is_junction(), "TARGET_PARENT_LINK_OR_MISSING")
    require(not target.is_symlink() and not target.is_junction() and (not target.exists() or target.is_dir()), "TARGET_LINK_OR_FILE")
    require(target.resolve().is_relative_to(root.resolve()) and target != root/LEGACY, "TARGET_NOT_ISOLATED")
    return {"target_directory": CURRENT_TARGET, "legacy_target_preserved": True,
        "example": "formula_issuer_product_postgres_probe", "package": "hwpx-agent-cli",
        "new_target_created_by_this_audit": False, "compiler_run": False}


def prepare(reader, root, checkpoint, phase=lambda name: None):
    phase("baseline_and_review_evidence")
    build = reader.json(BASELINE)
    baseline, protected = baseline_contract(build)
    approved, helper_pins = reviewed_deltas(reader.json(DRIFT_AUDIT), reader.json(SUPERVISOR))
    require(all(reader.fresh_pin(name) == pin for name, pin in helper_pins.items()), "QUALIFIED_SUPERVISOR_SOURCE_DRIFT")
    helper = list(helper_pins.values())+[reader.fresh_pin(name) for name in EXTRA]
    require(len(helper) == len({pin["path"] for pin in helper}) == 19, "HELPER_INVENTORY")
    phase("current_source842")
    current, changed = bind_current_sources(reader, baseline, approved)
    phase("historical_source817_parent_preimage")
    old_build = reader.json(HISTORICAL)
    require(old_build["state"] == "PASS_SOURCE_ONLY_NOT_GATE", "HISTORICAL_SOURCE_BUILD_MISSING")
    old = inventory(old_build["source_freeze"], 817)
    verify_historical_parent(reader, old)
    for name, pin in old.items():
        if name != PARENT:
            require(reader.fresh_pin(name) == approved.get(name, pin), "HISTORICAL_UNREVIEWED_DRIFT")
    direct = reader.json("implementation/p09/evidence/p09-142-root-crypto.source-progress.v1.json")
    require(all(reader.fresh_pin(pin_shape(pin)["path"]) == pin for pin in direct["verified_direct_pins"]), "ROOT_CRYPTO_DIRECT_PIN_DRIFT")
    history = historical_receipts(root)
    phase("historical_protected_closure")
    require(protected_closure(reader, history) == protected, "HISTORICAL_PROTECTED_CLOSURE_DRIFT")
    phase("protected_executable50")
    for name, pin in protected.items():
        require(reader.fresh_pin(name) == pin, "PROTECTED_EXECUTABLE_DRIFT")
    phase("whole_workspace_rust_inventory")
    actual_rust = rust_inputs(root, checkpoint)
    require(actual_rust and actual_rust.issubset(baseline), "WHOLE_WORKSPACE_RUST_COVERAGE_DRIFT")
    candidate_target = target_contract(root)
    baseline_pin = reader.pin(BASELINE)
    review_pins = [reader.pin(DRIFT_AUDIT), reader.pin(SUPERVISOR)]
    phase("final_fresh_hash_all_inputs")
    reader.finish()
    require(historical_receipts(root) == history, "HISTORY_INVENTORY_CHANGED")
    require(rust_inputs(root, checkpoint) == actual_rust, "RUST_INVENTORY_CHANGED")
    require(target_contract(root) == candidate_target, "TARGET_CONTRACT_CHANGED")
    phase("current_candidate_bound_not_compiled")
    return {"source_freeze": current, "source_freeze_exact_after": True,
        "build_helper_freeze": helper, "build_helper_freeze_exact_after": True,
        "protected_executables": list(protected.values()), "protected_executables_exact_after": True,
        "declared_source_delta_paths": changed, "whole_workspace_Rust_input_coverage_enforced": True,
        "whole_workspace_Rust_inputs": len(actual_rust), "historical_parent_archive_verified": True,
        "historical_source_inventory": 817, "historical_protected_closure_exact": True,
        "target_contract": candidate_target, "baseline_build_pin": baseline_pin,
        "reviewed_delta_evidence_pins": review_pins}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    args = parser.parse_args()
    require(Path.cwd().resolve() == c.ROOT, "WRONG_ROOT")
    destination = c.ROOT/f"implementation/p09/evidence/p09-149-current-issuer-build-inputs.run{args.run:02}.v1.json"
    require(not destination.exists() and destination.parent.is_dir() and not destination.parent.is_symlink()
        and not destination.parent.is_junction(), "FRESH_RECEIPT_REQUIRED")
    resources = PercentageResources()
    started = time.monotonic()
    reader = mutex = None
    lock_owned = False
    row = {"schema_version": "hwpx-agent.p09-current-issuer-build-inputs/v1", "state": "STOPPED_OR_FAILED_NOT_ACCEPTED",
        "current_build_input_candidate_accepted": False, "compiler_build_binding_accepted": False,
        "actual_build_SQL_Docker_Cargo_native_or_child_run": False, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "product_complete": False, "samples": resources.samples,
        "mutex_cleanup_confirmed": False, "error_code": None, "operation_phase": "admission"}
    try:
        ctypes.set_last_error(0)
        mutex = resources.windows.k.CreateMutexW(None, True, MUTEX)
        duplicate = ctypes.get_last_error() == 183
        require(mutex, "LOCK_FAILED")
        lock_owned = not duplicate
        require(lock_owned, "ALREADY_RUNNING")
        resources.admit()
        def checkpoint():
            require(time.monotonic()-started <= 600, "SCOPE_TIME_LIMIT")
            resources.checkpoint_io()
        reader = BuildInputReader(c.ROOT, checkpoint)
        row.update(prepare(reader, c.ROOT, checkpoint, lambda name: row.update(operation_phase=name)))
        row["state"] = "PASS_CURRENT_BUILD_INPUTS_ONLY_NOT_COMPILE_SQL_PRODUCT_OR_GATE"
        row["current_build_input_candidate_accepted"] = True
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, ValueError) else "CURRENT_ISSUER_OBSERVATION_OR_INPUT_FAILURE"
        row["error_code"] = code if re.fullmatch(r"[A-Za-z0-9_]+", code) else "CURRENT_ISSUER_REDACTED_FAILURE"
    finally:
        failed = False
        if mutex is not None:
            if lock_owned and not resources.windows.k.ReleaseMutex(mutex):
                failed = True
            if not resources.windows.k.CloseHandle(mutex):
                failed = True
        row["mutex_cleanup_confirmed"] = not failed
        if failed or resources.stop.is_set():
            row["state"] = "STOPPED_OR_FAILED_NOT_ACCEPTED"
            row["current_build_input_candidate_accepted"] = False
            row["error_code"] = resources.reason or "CURRENT_ISSUER_LOCK_CLEANUP_FAILED"
        resources.done.set()
        if reader is not None:
            row["bounded_input_IO"] = {"read_passes": reader.read_passes, "bytes_read": reader.bytes_read,
                "bound_inputs": len(reader.snapshots), "final_fresh_hashes": reader.final_fresh_hashes,
                "chunk_bytes": CHUNK_BYTES, "parse_budget_bytes": MAX_PARSE_BYTES,
                "read_bytes_per_second": READ_BYTES_PER_SECOND}
        row["elapsed_seconds"] = round(time.monotonic()-started, 4)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({"state": row["state"], "error_code": row["error_code"],
            "source_count": len(row.get("source_freeze", [])), "protected_count": len(row.get("protected_executables", [])),
            "declared_delta_count": len(row.get("declared_source_delta_paths", [])), "elapsed_seconds": row["elapsed_seconds"]}))
    return 0 if row["current_build_input_candidate_accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
