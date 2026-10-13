"""P09 case112: bounded source/artifact admission audit, not a product run.

기존 P340 reader/CPU·RAM/byte pacing/final freshness/cleanup을 재사용한다.
사용자 소스, 기존 binary, 완료111 증거를 변경하지 않는다. 새 receipt만 생성한다.
이 검사는 전체 Rust inventory, compile provenance 또는 Native atomic frame을 증명하지 않는다.
"""
import argparse
import json
from pathlib import Path

import close_p340_post_product_source_frame as source

SELF = "tools/p09/audit_case112_source_epoch.py"
TEST = "tools/p09/tests/test_case112_source_epoch.py"
MODULE = "crates/product-cli/src/reference_validation_product.rs"
LIBRARY = "crates/product-cli/src/lib.rs"
REGISTRATION = "pub mod reference_validation_product;"
FRESH_PIN = dict(path="implementation/p09/evidence/locked-r07/p340-light-review-run131.v1.json",
    bytes=94990, sha256="6d05cb6bf810ff5c19c61d1bc2d76921a00abb00d0f959c51e5fed9402a782ff")
PASS = "PASS_CASE112_SOURCE_EPOCH_AUDIT_NOT_COMPILE_RUNTIME_OR_GATE"


def require(ok, code):
    if not ok:
        raise ValueError("P09_CASE112_EPOCH_" + code)


def epoch_decision(frozen_library, current_library, frozen_binary, current_binary,
                   module_pin, frozen_paths, registration_present, registration_only_delta):
    require(frozen_library["path"] == current_library["path"] == LIBRARY,
            "EXACT_LIBRARY_PATH")
    require(frozen_binary == current_binary and frozen_binary["path"] in frozen_paths,
            "FROZEN_TEST_ARTIFACT_DRIFT")
    require(module_pin["path"] == MODULE and type(module_pin["bytes"]) is int
            and 0 < module_pin["bytes"] <= 1048576,
            "BOUNDED_REGISTERED_MODULE")
    require(type(registration_present) is bool and type(registration_only_delta) is bool,
            "EXACT_REGISTRATION_OBSERVATIONS")
    same = frozen_library == current_library
    added = MODULE not in frozen_paths
    if same:
        decision = "NO_LIBRARY_EPOCH_DRIFT_NOT_BUILD_OR_PRODUCT_QUALIFICATION"
    elif added and registration_present and registration_only_delta:
        decision = "REGISTERED_MODULE_ADDED_REQUIRES_CURRENT_BUILD_EPOCH"
    else:
        decision = "ADDITIONAL_LIBRARY_DRIFT_REQUIRES_EXPLICIT_SOURCE_EPOCH_REVIEW"
    return dict(decision=decision, library_matches_frozen_runtime_source=same,
        new_module_absent_from_frozen_source=added,
        registration_line_present=registration_present,
        normalized_library_delta_is_registration_only=registration_only_delta,
        existing_test_binary_bytes_preserved=True,
        current_module_compile_binding_qualified=False,
        full_current_Rust_inventory_qualified=False,
        actual112_admitted_by_this_audit=False,
        input_pin_rebased_or_source_overwritten=False)


def validate(row):
    require(row["state"] == PASS and row["prior_queue_cases"] == 105
            and row["next_case"] == 112 and row["bound_queue_fresh_pin"] == FRESH_PIN,
            "EXACT_COMPLETED111_NEXT112")
    require(row["preparation_IO"]["finished"] is True
            and row["preparation_IO"]["bound_inputs"] == row["preparation_IO"]["final_fresh_hashes"]
            and row["resource_watcher_cleanup_confirmed"] is True
            and row["resource_stop_reason"] is None,
            "ACTUAL_ALL_INPUTS_FINAL_FRESH_AND_CLEANUP")
    require(all(row[key] is False for key in (
        "actual_product_child_executed", "Native_frame_started", "Cargo_started",
        "runtime_acceptance_changed", "product_complete", "PC_freeze_resolved"))
        and row["accepted_count_delta"] == 0
        and row["P09_gate"] == row["A12_gate"] == row["A13_gate"] == "OPEN",
        "AUDIT_NEVER_PRODUCT_OR_GATE")
    require(row["epoch_decision"] == epoch_decision(row["frozen_library_pin"],
        row["current_library_pin"], row["frozen_binary_pin"], row["current_binary_pin"],
        row["current_module_pin"], set(row["frozen_source_paths"]),
        row["registration_line_present"], row["registration_only_normalized_delta"]),
        "DECISION_RECOMPUTED_FROM_BOUND_OBSERVATIONS")


def run(number):
    import resume_preserved106_queue_runtime as runtime
    root = runtime.p.c.ROOT
    require(Path.cwd().resolve() == root and type(number) is int and 1 <= number <= 999,
            "ROOT_AND_FRESH_RUN_RANGE")
    destination = root / "implementation/p09/evidence" / f"p09-361-case112-source-epoch-run{number:03}.v1.json"
    require(not destination.exists(), "FRESH_RECEIPT_ONLY")
    context = runtime.g.observation.Context()
    owner = runtime.g.observation.Resources(context)
    q = proposed = None
    stage = "admission"
    out = runtime.p.r.flags()
    out.update(schema_version="hwpx-agent.p09-case112-source-epoch-audit/v1",
        state="FAILED_NOT_ACCEPTED", bound_queue_fresh_pin=FRESH_PIN,
        actual_product_child_executed=False, Native_frame_started=False, Cargo_started=False,
        runtime_acceptance_changed=False, accepted_count_delta=0)
    try:
        owner.admit()
        q = runtime.MetadataReader(owner, context)
        stage = "queue_binding"
        fresh = q.json(FRESH_PIN["path"])
        require(q.reader.snapshots[FRESH_PIN["path"]] == FRESH_PIN
                and fresh["state"] == runtime.FRESH
                and fresh["prior_runtime_plan"]["runtime_source_qualified_individual_cases"] == 105
                and fresh["selected_test_index"] == 112,
                "EXACT_AUTHORITATIVE_FRESH105_NEXT112")
        for pin in fresh["current95_code_pins"]:
            if pin["path"] in (runtime.SELF, runtime.TEST):
                require(q.pin(pin["path"]) == pin, "QUALIFIED_SCANNER_CODE_DRIFT")
        body = q.json(source.BODY_PIN["path"])
        require(q.reader.snapshots[source.BODY_PIN["path"]] == source.BODY_PIN,
                "ORIGINAL_EXECUTED_SOURCE_MANIFEST")
        frozen = source.pins(body["source_freeze"])
        require(len(frozen) == 1658 and frozen[LIBRARY] == source.FROZEN_MUTABLE_PINS[0],
                "EXACT_FROZEN_LIBRARY_INPUT")
        stage = "source_and_binary_observation"
        binary_pin = runtime.p.m.EXE
        require(frozen.get(binary_pin["path"]) == binary_pin, "FROZEN_BINARY_INPUT")
        current_binary = q.pin(binary_pin["path"])
        archive = source.ARCHIVE_BINDINGS[0]["archive_pin"]
        old_text = q.text(archive["path"])
        require(q.reader.snapshots[archive["path"]] == archive, "EXACT_ORIGINAL_LIBRARY_ARCHIVE")
        current_text = q.text(LIBRARY)
        current_library = q.reader.snapshots[LIBRARY]
        module_pin = q.pin(MODULE)
        lines = current_text.splitlines(keepends=True)
        registrations = [line for line in lines if line.rstrip("\n") == REGISTRATION]
        registration_present = len(registrations) == 1
        stripped = "".join(line for line in lines if line.rstrip("\n") != REGISTRATION)
        only_delta = registration_present and stripped == old_text
        decision = epoch_decision(frozen[LIBRARY], current_library, binary_pin,
            current_binary, module_pin, set(frozen), registration_present, only_delta)
        for name in (SELF, TEST, "Cargo.toml", "Cargo.lock", "crates/product-cli/Cargo.toml"):
            q.pin(name)
        out.update(prior_queue_cases=105, next_case=112,
            frozen_library_pin=frozen[LIBRARY], current_library_pin=current_library,
            frozen_binary_pin=binary_pin, current_binary_pin=current_binary,
            current_module_pin=module_pin, frozen_source_paths=sorted(frozen),
            registration_line_present=registration_present,
            registration_only_normalized_delta=only_delta, epoch_decision=decision)
        stage = "final_fresh_preparation"
        q.finish()
        proposed = dict(state=PASS)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        out["error_code"] = runtime.p.b.run.original.closed_error(error)
        out["failure_diagnostic"] = runtime.m.m.diagnostic(error, stage)
    finally:
        if q is not None:
            q.close_entry()
            out["preparation_IO"] = q.summary()
            out["bound_input_pins"] = list(q.reader.snapshots.values())
        runtime.m.complete_runtime(out, owner, proposed, validate if proposed else lambda row: None)
        out["metadata_observation"] = runtime.g.observation.summary(owner)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as stream:
            output = runtime.m.PinningOutput(stream)
            runtime.r.compact.dump(out, output,
                checkpoint=lambda: require(owner.done.is_set(), "TERMINAL_OUTPUT_ONLY"), indent=2)
            pin = dict(path=destination.relative_to(root).as_posix(),
                bytes=output.written, sha256=output.digest.hexdigest())
        print(json.dumps(dict(state=out["state"], receipt_pin=pin,
            decision=out.get("epoch_decision", {}).get("decision"),
            error_code=out.get("error_code"), resource_stop_reason=out.get("resource_stop_reason"))))
    return 0 if out["state"] == PASS else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=int)
    return run(parser.parse_args().run)


if __name__ == "__main__":
    raise SystemExit(main())
