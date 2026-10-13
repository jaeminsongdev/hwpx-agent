"""Explicit compound129 authority and the REAL flat case130 predecessor branch.

원 STOP root를 일반 Native PASS로 바꾸지 않는다. 기존 runtime/worker/GO/Job,
full Native oracle·CPU/RAM·600s·pacing·typed observations는 유지한다.
129 수용기는 기존 수용경계처럼 현재 Rust787/EXE/helper를 fresh 결속한다.
과거 전체입력 두 byte 경계는 source002의 실제 증거이며 재실행하지 않는다.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import threading
import time
from types import FunctionType, SimpleNamespace as NS

import validate_flat_case129_compound_observer_v2 as contract

source = contract.source.runtime
base, a, c = source.base, source.a, source.c
SELF = "tools/p09/flat_preserved129_compound_connection_v1.py"
TEST = "tools/p09/tests/test_flat_preserved129_compound_connection_v1.py"
FILES = (SELF, TEST, contract.SELF, contract.TEST, contract.prior.SELF, contract.prior.TEST)
CONTROLLERS = tuple(dict.fromkeys(source.CONTROLLERS + FILES))
SCHEMA = "hwpx-agent.p09-preserved129-compound-authority/v1"
PASS = "PASS_EXACT129_DISTINCT_BODY_AND_SOURCE_ACCEPTED_ONCE_NOT_FULL249_OR_GATE"
KIND = "preserved129_body_with_independent_full_source002"
OUTPUT = "implementation/p09/evidence/p09-361-case129-current-epoch-accept001.v1.json"
QUAL_PATH = "implementation/p09/evidence/p09-361-case129-compound-connection-code-r324.v1.json"
CONTRACT_QUAL_PIN = dict(path="implementation/p09/evidence/p09-361-case129-compound-observer-v2-contracts-r321.v1.json",
    bytes=2448, sha256="0f0576fa65334a160ee8a09ef69dfdae8a8c5ca24d91d1725b920692809752b7")
ORIGINAL_COMPOUND_QUAL_PIN = dict(path="implementation/p09/evidence/p09-361-case129-compound-code-contracts-r309.v1.json",
    bytes=5008, sha256="0f55ae2d7ab8e660645c7548fecc70c777bd743fd86b80adf2893d96089d1854")


def require(ok, code):
    if not ok:
        raise ValueError("COMPOUND_CONNECTION_" + code)


def qualification(q, pin):
    require(pin.get("path") == QUAL_PATH, "EXACT_CONNECTION_QUAL_PATH")
    base.scope.pins([pin], 1)
    row = a.read_exact(q, pin)
    a.fields(row, dict(state="PASS_COMPOUND129_AUTHORITY_AND_NEXT130_CODE_NOT_ACTUAL_ACCEPTANCE",
        accepted_count_after=122, accepted_count_delta=0, cleanup_confirmed=True,
        product_body_replayed=False, Native_source_replayed=False,
        next130_production_entry_dependencies_qualified=True), "CONNECTION_CODE_NOT_QUEUE_PASS")
    a.fields(row["contracts"], dict(errors=0, failures=0, skipped=0), "NO_FAILED_CODE_CONTRACTS")
    require(type(row["contracts"]["run"]) is int and row["contracts"]["run"] >= 20, "COMPLETE_CODE_CONTRACTS")
    pins = base.scope.pins(row["new_code_pins"], 2)
    require(set(pins) == {SELF, TEST}, "EXACT_CONNECTION_CODE2")
    for name, expected in pins.items():
        a.exact(q.pin(name), expected, "CURRENT_TESTED_CONNECTION_CODE")
    return row


def documents(q):
    """Fresh receipt/code binding, full original pure oracle; NEVER authority."""
    s = contract.source
    row = a.read_exact(q, contract.SOURCE_PIN)
    previous = a.read_exact(q, contract.PREVIOUS_PIN)
    connected = a.read_exact(q, contract.CONNECTION_PIN)
    observed = a.read_exact(q, contract.OBSERVER_PIN)
    real = a.read_exact(q, contract.REAL_PIN)
    sq = a.read_exact(q, contract.prior.QUAL_PIN)
    cq = a.read_exact(q, CONTRACT_QUAL_PIN)
    oldcq = a.read_exact(q, ORIGINAL_COMPOUND_QUAL_PIN)
    a.fields(sq, dict(source_contracts_passed=29, errors=0, failures=0, skipped=0,
        cleanup_confirmed=True), "ORIGINAL_SOURCE29")
    a.exact(cq["contracts"], dict(run=30, errors=0, failures=0, skipped=0), "COMPOUND_OBSERVER30")
    a.exact(oldcq["contracts"], dict(run=28, errors=0, failures=0, skipped=0), "ORIGINAL_COMPOUND28")
    for pin in sq["source_controller_pins"] + cq["new_code_pins"] + oldcq["new_contract_code_pins"] + connected["new_code_pins"] + \
            observed["new_code_pins"] + observed["unchanged_dependency_pins"] + real["bound_source_pins"]:
        a.exact(q.pin(pin["path"]), pin, "ALL_QUALIFIED_DEPENDENCIES")
    required = base.scope.pins(row["required_source_pins"])
    original = a.read_exact(q, s.STOP_PIN)
    authority = a.read_exact(q, s.AUTHORITY_PIN)
    listing = a.read_exact(q, base.scope.LIST_PIN)
    candidate = contract.validate(original, s.STOP_PIN, row, contract.SOURCE_PIN,
        authority, s.AUTHORITY_PIN, listing, sq, contract.prior.QUAL_PIN,
        previous, connected, observed, real, q.checkpoint)
    a.resource_history(authority["resource_samples"])
    return row, original, listing, required, candidate


def parent_header(row, step):
    require(step.index == 130 and step.before == 123, "ONLY_EXPLICIT_NEXT130_COMPOUND_BRANCH")
    require(row.get("synthetic_fixture_only_not_evidence", False) is False, "NO_SYNTHETIC_AUTHORITY")
    a.fields(row, dict(schema_version=SCHEMA, state=PASS, acceptance_kind=KIND,
        accepted_count_before=122, accepted_count_after=123, accepted_count_delta=1,
        accepted_test_indices=[129], accepted_test_names=[contract.source.CASE],
        accepted_current_generation_case_count=18, next_runtime_index=130,
        runtime_remaining_individual_cases=126, resource_cleanup_confirmed=True,
        product_and_source_epochs_distinct=True, Native_product_single_frame_qualified=False,
        original_failed_root_state_rewritten=False, successful_product_cases_reexecuted=False,
        product_child_executed=False, Native_frame_reexecuted=False,
        prior105_historical_epochs_preserved=True, prior105_current_generation_rebased=False,
        duplicate_acceptance_refuses_overwrite=True, full249_current_qualified=False,
        signed16_current_qualified=False, whole_runtime_reconciliation_required=True,
        P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN", P10_started=False,
        sole_serial_sampler=True, parallel_observer_started=False), "EXPLICIT_COMPOUND_PARENT")
    require("runtime_candidate_pin" not in row, "NO_ORDINARY_NATIVE_PASS_ALIAS")
    a.exact(row["preserved_failed_product_root_pin"], contract.source.STOP_PIN, "ORIGINAL_STOP_NOT_NATIVE_PASS")
    a.exact(row["independent_full_source_pin"], contract.SOURCE_PIN, "EXACT_COMMITTED_SOURCE002")
    a.exact(row["prior_queue_authority_pin"], contract.source.AUTHORITY_PIN, "PRIOR122_AUTHORITY")
    a.exact(step.prior_candidate_pin, contract.source.STOP_PIN, "STEP_REFERS_TO_PRESERVED_BODY_ONLY")
    require(step.prior_queue_pin["path"] == OUTPUT, "CANONICAL_COMPOUND_AUTHORITY_PATH")
    a.exact(row["accepted_epoch_key"], contract.source.STOP_PIN["sha256"] + ":129:source:" +
        contract.SOURCE_PIN["sha256"], "ONCE_ONLY_DISTINCT_EPOCH_KEY")
    fresh = base.scope.pins(row["fresh_input_pins"])
    n = len(fresh)
    require(type(row["fresh_read_passes"]) is int and row["fresh_read_passes"] >= 2 * n and
        type(row["fresh_bytes_read"]) is int and row["fresh_bytes_read"] >= 2 * sum(p["bytes"] for p in fresh.values()),
        "ALL_PRIOR_ACCEPTANCE_FRESH_READS")
    a.exact(row["final_fresh_hashes"], n, "ALL_PRIOR_FINAL_HASHES")
    a.fields(row, dict(file_open_ceiling_per_second=20,
        qualifier_read_rates_by_kind=dict(binary=1048576, other=2097152)), "ORIGINAL_ACCEPTANCE_RATES")
    a.resource_history(row["resource_samples"])
    return fresh


def predecessor_data_path(index):
    require(index == 130, "ONE_COMPOUND_PREDECESSOR_DATA")
    return "implementation/p09/evidence/p09-361-case130-compound-predecessor-data001.v1.json"


def predecessor_data(q, step):
    text = q.text(predecessor_data_path(step.index))
    require(0 < len(text.encode("utf-8")) <= 16384, "BOUNDED_PREDECESSOR_DATA")
    row = json.loads(text, object_pairs_hook=base.unique)
    require(type(row) is dict and set(row) == {"schema_version", "index", "before", "acceptance_kind",
        "base_step_pin", "prior_authority_pin", "preserved_body_pin", "full_source_pin",
        "connection_qualification_pin"}, "CLOSED_PREDECESSOR_DATA")
    a.fields(row, dict(schema_version="hwpx-agent.p09-compound-predecessor/v1", index=130,
        before=123, acceptance_kind=KIND, base_step_pin=step.pin,
        prior_authority_pin=step.prior_queue_pin, preserved_body_pin=contract.source.STOP_PIN,
        full_source_pin=contract.SOURCE_PIN), "NEXT130_DATA_BINDING")
    qualification(q, row["connection_qualification_pin"])
    return row


def binding(q):
    step = base.CONFIG
    require(step is not None and step.index == 130, "EXPLICIT_COMPOUND_STEP130")
    a.exact(q.pin(step.path), step.pin, "CURRENT_IMMUTABLE_STEP130")
    data = predecessor_data(q, step)
    parent = a.read_exact(q, step.prior_queue_pin)
    fresh = parent_header(parent, step)
    a.exact(parent["connection_qualification_pin"], data["connection_qualification_pin"], "SAME_TESTED_NEXT130_BRANCH")
    row, original, listing, required, candidate = documents(q)
    a.exact(parent["actual_compound_evidence_validation"], candidate, "SAME_FULL_COMPOUND_ORACLE")
    require(listing["source_test_names"][129] == step.case and
        listing["source_test_names"][128] == parent["accepted_test_names"][0], "EXACT_COMPILED_CASE130")
    required = base.scope.extend(required, fresh)
    # 기존 qualified flat binding의 전체 bootstrap/code/archive를 보존한다.
    for pin in original["bootstrap_metadata"]["input_pins"]:
        a.exact(q.pin(pin["path"]), pin, "ALL_INHERITED_PRODUCT_BOOTSTRAP")
    for name in (base.stable.SELF, base.stable.TEST, base.stable.handoff.SELF, base.stable.handoff.TEST,
            base.stable.final_sample.SELF, base.accepted115.SELF, base.accepted115.TEST):
        a.exact(q.pin(name), required[name], "QUALIFIED115_CODE")
        archive = "implementation/p09/evidence/p361-case115-qualified-code/" + name
        a.exact(q.pin(archive), dict(required[name], path=archive), "QUALIFIED115_ARCHIVE")
    current = base.scope.listing_inputs(listing)
    rust = {n for n in current if n.startswith(("crates/", "protocol/generated/rust/", "tools/xtask/"))
        and (n.endswith(".rs") or n.endswith("/Cargo.toml"))}
    require(len(rust) == 787 and required[base.scope.EXE_PIN["path"]] == base.scope.EXE_PIN, "CURRENT_RUST787_EXE")
    return base.scope.extend(required, q.snapshots), rust


def binding_attempt(q, run):
    require(base.CONFIG is not None and base.CONFIG.index == 130 and run == 1, "ONE_EXPLICIT_CASE130_RUN")
    source.reviewed_inputs(q, run)
    return binding(q)


def template():
    engine, proof = source.template()
    require(engine.run_owned.__globals__["SELF"] == source.SELF, "UNCHANGED_SOURCE_STAT_TEMPLATE")
    engine.run_owned.__globals__.update(SELF=SELF, TEST=TEST)
    engine.worker.__globals__.update(SELF=SELF, TEST=TEST)
    return engine, dict(proof, explicit_compound_predecessor_controller=True,
        source_engine_bytecode_unchanged=True, default_module_functions_mutated=False)


def context(step):
    return NS(**{**vars(source.context(step)), "SELF": SELF, "TEST": TEST})


def worker(task):
    a.exact(base.run_for(task), 1, "EXACT_FIRST_WORKER")
    engine, _ = template()
    return engine.worker(task)


def run_owned(run):
    require(base.CONFIG is not None and base.CONFIG.index == 130 and run == 1, "ONE_PRODUCT130_ATTEMPT")
    env = dict(source.run_owned.__globals__, template=template, binding_attempt=binding_attempt)
    return FunctionType(source.run_owned.__code__, env, argdefs=source.run_owned.__defaults__)(run)


def preflight_projection(raw, leaf):
    fn = source.preflight_projection(raw, leaf)
    fn.__globals__.update(SELF=SELF, TEST=TEST, template=template, binding_attempt=binding_attempt)
    return fn


def preflight():
    return FunctionType(source.preflight.__code__, dict(source.preflight.__globals__,
        preflight_projection=preflight_projection), argdefs=source.preflight.__defaults__)()


def validator(raw, ctx, flat=True):
    fn, proof = source.validator(raw, ctx, flat)
    fn.__globals__["CONTROLLERS"] = tuple(dict.fromkeys(fn.__globals__["CONTROLLERS"] + FILES))
    return fn, dict(proof, compound_controller_code_inside_complete_Native_frame=True)


def validate_candidate(q, row, listing, body, fresh, ctx, flat=True):
    env = dict(source.validate_candidate.__globals__, validator=validator)
    return FunctionType(source.validate_candidate.__code__, env,
        argdefs=source.validate_candidate.__defaults__)(q, row, listing, body, fresh, ctx, flat)


def prepare_projection(raw):
    require(base.CONFIG is not None and base.CONFIG.index == 130, "EXACT_ACCEPT130_BRANCH")
    fn = source.prepare_projection(raw)
    # The unchanged prepare code uses PASS exactly once as the EXPECTED parent
    # kind. It now expects explicit compound PASS; no receipt is rewritten.
    require(fn.__globals__["PASS"] == source.prior.accepted.original.PASS, "ORIGINAL_NORMAL_PARENT_KIND")
    fn.__globals__.update(PASS=PASS, validate_candidate=validate_candidate,
        r=NS(**{**vars(fn.__globals__["r"]), "context": context}))
    return fn


def prepare(q, root_pin):
    source.reviewed_inputs(q, 1)
    inherited, _ = binding(q)  # BEFORE reading current root: no self-pin cycle.
    env = dict(source.prepare.__globals__, prepare_projection=prepare_projection)
    row, listing, evidence, proof = FunctionType(source.prepare.__code__, env,
        argdefs=source.prepare.__defaults__)(q, root_pin)
    expected = base.scope.pins(row["source_freeze"])
    for name, pin in inherited.items():
        a.exact(expected.get(name), pin, "COMPLETE_COMPOUND_PREDECESSOR_IN_NEW_NATIVE_FRAME")
    return row, listing, evidence, dict(proof, explicit_compound_parent_validated=True)


def accept130(root_pin):
    require(base.CONFIG is not None and base.CONFIG.index == 130, "ONLY_ACCEPT130")
    env = dict(source.accept.__globals__, SELF=SELF, TEST=TEST, CONTROLLERS=CONTROLLERS,
        context=context, prepare=prepare)
    return FunctionType(source.accept.__code__, env, argdefs=source.accept.__defaults__)(root_pin)


def imported(q, required):
    names = {SELF, TEST}
    for module in tuple(sys.modules.values()):
        path = getattr(module, "__file__", None)
        if path:
            path = Path(path).absolute()
            if path.is_relative_to(c.ROOT / "tools/p09") and path.suffix == ".py":
                names.add(path.relative_to(c.ROOT).as_posix())
    require(len(names) <= 64, "ORIGINAL_HELPER64_CEILING")
    for name in sorted(names):
        pin = q.pin(name)
        if name in required:
            a.exact(pin, required[name], "CURRENT_INHERITED_HELPER")
        else:
            require(name in FILES, "ONLY_QUALIFIED_NEW_CONNECTION_HELPERS")
    return names


def scan_future(q, start=129):
    """Exact bounded authority paths; original20/s pacing, no Git/full-tree scan."""
    require(start in (129, 130), "BOUNDED_LIVE_QUEUE_SCAN")
    observations = 0
    for index in range(start, 250):
        for suffix in ("current-epoch-accept001", "compound-epoch-accept001"):
            q.open_pacer.reserve()
            path = c.ROOT / f"implementation/p09/evidence/p09-361-case{index}-{suffix}.v1.json"
            try:
                path.lstat()  # 단일 fresh stat; broken link도 존재하면 거부한다.
            except FileNotFoundError:
                pass
            else:
                require(False, "LIVE_FUTURE_OR_DUPLICATE_AUTHORITY")
            observations += 1
    return dict(first_index=start, last_index=249, exact_path_observations=observations,
        original_request_limit_per_second=20, no_other_authority_observed=True)


def accept129(code_pin):
    """Actual independently guarded acceptance; body/full Native NEVER replay."""
    destination = c.ROOT / OUTPUT
    require(not destination.exists() and not destination.is_symlink(), "IMMUTABLE_ACCEPT_ALREADY_EXISTS")
    g = a.Guard(); q = bridge = result = None; error = None; started = time.monotonic()
    try:
        g.acquire(); q = a.AcceptanceReader(c.ROOT, g.check)
        bridge = source.prior.prior.metadata.MetadataCheckpoint(q,
            NS(lock=threading.Lock(), samples=g.samples, checkpoint_io=g.check))
        qualification(q, code_pin)
        initial_scan = scan_future(q)
        row, original, listing, required, candidate = documents(q)
        current = base.scope.listing_inputs(listing)
        rust = {n for n in current if n.startswith(("crates/", "protocol/generated/rust/", "tools/xtask/"))
            and (n.endswith(".rs") or n.endswith("/Cargo.toml"))}
        require(len(rust) == 787, "CURRENT_RUST787")
        inventory_name = "tools/p09/current_issuer_build_inputs.py"
        raw = q.text(inventory_name)
        a.exact(q.snapshots[inventory_name], required[inventory_name], "ORIGINAL_RUST_ENUMERATOR")
        inventory = base.native.definitions(raw, ("rust_inputs",), dict(os=os, Path=Path, require=require))
        require(inventory.rust_inputs(c.ROOT, q.open_pacer.reserve) == rust, "FIRST_WHOLE_RUST787")
        names = rust | set(row["imported_controller_paths"]) | set(original["imported_worker_source_paths"]) | {base.scope.EXE_PIN["path"]}
        for name in sorted(names):
            a.exact(q.pin(name), required[name], "ALL_CURRENT_COMPILED_AND_EXECUTED_HELPERS")
        helpers = imported(q, required)
        q.finish()
        require(inventory.rust_inputs(c.ROOT, q.open_pacer.reserve) == rust, "FINAL_WHOLE_RUST787")
        final_scan = scan_future(q)
        time.sleep(.5); g.check(force=True)
        result = dict(schema_version=SCHEMA, state=PASS, acceptance_kind=KIND,
            preserved_failed_product_root_pin=contract.source.STOP_PIN,
            independent_full_source_pin=contract.SOURCE_PIN, prior_queue_authority_pin=contract.source.AUTHORITY_PIN,
            connection_qualification_pin=code_pin, current_compiled_listing_pin=base.scope.LIST_PIN,
            accepted_epoch_key=contract.source.STOP_PIN["sha256"] + ":129:source:" + contract.SOURCE_PIN["sha256"],
            accepted_test_indices=[129], accepted_test_names=[contract.source.CASE],
            accepted_count_before=122, accepted_count_delta=1, accepted_count_after=123,
            runtime_remaining_individual_cases=126, next_runtime_index=130,
            accepted_current_generation_case_count=18, prior105_historical_epochs_preserved=True,
            prior105_current_generation_rebased=False, duplicate_acceptance_refuses_overwrite=True,
            product_and_source_epochs_distinct=True, Native_product_single_frame_qualified=False,
            original_failed_root_state_rewritten=False, product_child_executed=False,
            Native_frame_reexecuted=False, successful_product_cases_reexecuted=False,
            actual_compound_evidence_validation=candidate, current_Rust_input_count=787,
            current_Rust_inventory_checked_before_after=True, live_queue_scans=[initial_scan, final_scan],
            fresh_input_pins=list(q.snapshots.values()), qualifier_imported_source_paths=sorted(helpers),
            fresh_read_passes=q.read_passes, fresh_bytes_read=q.bytes_read,
            final_fresh_hashes=q.final_fresh_hashes, file_open_ceiling_per_second=20,
            qualifier_read_rates_by_kind=dict(binary=1048576, other=2097152),
            fresh_qualifier_is_not_new_native_or_product_evidence=True,
            full249_current_qualified=False, signed16_current_qualified=False,
            whole_runtime_reconciliation_required=True, P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN",
            P10_started=False, PC_freeze_resolved=False)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        error = str(exc) if isinstance(exc, ValueError) else "REDACTED_COMPOUND_ACCEPTANCE_FAILURE"
    finally:
        if bridge:
            bridge.restore()
        g.close()
    if error or result is None or not g.cleanup:
        print(json.dumps(dict(state="STOPPED_COMPOUND_NOT_ACCEPTED", error_code=error,
            cleanup_confirmed=g.cleanup, accepted_count_after=122, accepted_count_delta=0)))
        return 2
    result.update(resource_samples=g.samples, resource_cleanup_confirmed=True,
        sole_serial_sampler=True, parallel_observer_started=False,
        metadata_guard=bridge.summary(), elapsed_seconds=time.monotonic()-started)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=True, indent=2)
    print(json.dumps(dict(state=PASS, accepted=123, remaining=126, next_case=130, cleanup_confirmed=True)))
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1:3] == ["--owned-worker", "--task"]:
        base.configure(base.task_index(sys.argv[3])); require(base.CONFIG.index == 130, "ONLY_WORKER130")
        raise SystemExit(worker(sys.argv[3]))
    parser = argparse.ArgumentParser()
    parser.add_argument("--accept-preserved129", action="store_true")
    parser.add_argument("--qualification-bytes", type=int)
    parser.add_argument("--qualification-sha256")
    parser.add_argument("--case", type=int)
    parser.add_argument("--run", type=int)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--accept", action="store_true")
    parser.add_argument("--root-bytes", type=int)
    parser.add_argument("--root-sha256")
    args = parser.parse_args()
    if args.accept_preserved129:
        require(args.case is None and args.run is None and not args.preflight and not args.accept,
            "ONE_PRESERVED129_MODE")
        pin = dict(path=QUAL_PATH, bytes=args.qualification_bytes, sha256=args.qualification_sha256)
        base.scope.pins([pin], 1); raise SystemExit(accept129(pin))
    require(args.case == 130 and args.qualification_bytes is None and args.qualification_sha256 is None,
        "EXPLICIT_NEXT130_MODE")
    base.configure(130)
    require(sum((args.run is not None, args.preflight, args.accept)) == 1, "ONE_NEXT130_MODE")
    if args.accept:
        pin = dict(path=source.root_path(base.CONFIG), bytes=args.root_bytes, sha256=args.root_sha256)
        base.scope.pins([pin], 1); raise SystemExit(accept130(pin))
    require(args.root_bytes is None and args.root_sha256 is None, "ROOT_ARGUMENTS_ACCEPT_ONLY")
    raise SystemExit(preflight() if args.preflight else run_owned(args.run))
