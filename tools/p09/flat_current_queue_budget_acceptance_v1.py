"""Same complete flat+metadata oracle, strengthened by actual budget factory.

Canonical reviewed125/run002 or later first001 only; no synthetic acceptance.
Every new controller/DATA/source pin must be inside the real whole Native frame.
"""
import argparse
import json
from types import FunctionType, SimpleNamespace as NS

import flat_current_queue_metadata_acceptance as metadata
import flat_current_queue_budget_runtime_v1 as runtime

original = metadata.original
a = metadata.a
SELF = runtime.ACCEPTOR
TEST = runtime.TEST
CONTROLLERS = tuple(dict.fromkeys(metadata.CONTROLLERS + runtime.FILES))


def require(ok, code):
    if not ok:
        raise ValueError("BUDGET_ACCEPT_" + code)


def root_path(step):
    return f"implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run{runtime.attempt(step.index):03}.v1.json"


def validator(raw, ctx, flat=True):
    project, proof = metadata.validator(raw, ctx, flat)
    project.__globals__["CONTROLLERS"] = tuple(dict.fromkeys(
        project.__globals__["CONTROLLERS"] + CONTROLLERS))
    return project, dict(proof, early_budget_controller_pins_added=True)


def actual_budget_binding(row):
    attribution = row["serial_CPU_attribution"]
    binding = attribution["early_budget_probe_connection"]
    a.fields(binding, dict(existing_observer_instances=1, budget_probe_instances=1,
        same_original_windows_factory=True, original_sample_CPU_RAM_values_retained=True,
        original_cold8_warning75_schedule_retained=True, original_close_and_summary_retained=True,
        second_sampler_thread_or_process=False, additional_PDH_query=False,
        original_K32_decisions_replaced=False, instance_binding_observed=True,
        runtime_product_connection_qualified=False, PC_freeze_resolved=False), "ACTUAL_SOLE_FACTORY")
    proof = binding["original_probe_sample_AST_projection"]
    a.fields(proof, dict(original_sample_AST_restored_exactly=True,
        original_native_collect_value_PID_status_close_and_final_budget_checks_retained=True,
        added_cost_sites=4, additional_clock_reads_only=True,
        extra_CPU_RAM_query_sampler_or_thread=False,
        original_maximum_sample_seconds=.05, original_maximum_total_seconds=2.0,
        OS_call_hard_preemption_guaranteed=False), "EXACT_EARLY_BUDGET_PROJECTION")
    probes = attribution["probes"]
    require(type(probes) is list and len(probes) == 1, "ONE_PROBE")
    a.fields(probes[0], dict(query_remaining=False, cleanup_confirmed=True,
        cost_checked_before_formatted_reads=True,
        original_seven_counter_PID_status_and_final_cost_checks_retained=True,
        original_CPU_RAM_guards_replaced=False, runtime_connection_qualified=False,
        PC_freeze_resolved=False), "BUDGET_PROBE_CLEANUP")
    require(type(probes[0]["early_budget_checks"]) is int and probes[0]["early_budget_checks"] > 0,
        "ACTUAL_EARLY_CHECKS_NOT_IMPORTED_ONLY")
    require(type(probes[0]["early_budget_stops"]) is int and probes[0]["early_budget_stops"] >= 0,
        "ACTUAL_STOP_COUNT")
    return True


def validate_candidate(q, row, listing, oldbody, fresh, ctx, flat=True):
    # Retain unchanged complete metadata validator, which itself retains all
    # original flat oracle predicates, adding only stronger controller pins.
    env = dict(metadata.validate_candidate.__globals__, validator=validator)
    unchanged = FunctionType(metadata.validate_candidate.__code__, env,
                             argdefs=metadata.validate_candidate.__defaults__)
    evidence, proof = unchanged(q, row, listing, oldbody, fresh, ctx, flat)
    actual_budget_binding(row)
    proof["actual_sole_early_budget_probe_binding_checked"] = True
    return evidence, proof


def prepare_projection(raw):
    # Existing counted root-path projection and exact undo retained unchanged;
    # explicit new root function and stronger validator replace dependencies.
    env = dict(metadata.prepare_projection.__globals__)
    env.update(root_path=root_path, validate_candidate=validate_candidate,
               runtime=runtime)
    unchanged = FunctionType(metadata.prepare_projection.__code__, env,
                             argdefs=metadata.prepare_projection.__defaults__)
    return unchanged(raw)


def prepare(q, root_pin):
    data = runtime.reviewed_inputs(q, runtime.attempt(original.r.CONFIG.index))
    source = q.text(original.SELF).encode("utf-8")
    qualification = a.read_exact(q, runtime.metadata.QUALIFIED)
    pins = {p["path"]: p for p in qualification["frozen_core_pins"]}
    a.exact(q.snapshots[original.SELF], pins[original.SELF], "FROZEN_FLAT_ACCEPTOR")
    row, listing, evidence, proof = prepare_projection(source)(q, root_pin)
    expected = original.r.scope.pins(row["source_freeze"])
    for pin in data["connection_code_pins"]:
        a.exact(expected[pin["path"]], pin, "NEW_CODE_IN_WHOLE_NATIVE_FRAME")
    for name in (runtime.data_path(original.r.CONFIG.index),
                 runtime.metadata.data_path(original.r.CONFIG.index)):
        a.exact(expected[name], q.snapshots[name], "BOTH_DATA_INSIDE_FRAME")
    for pin in (runtime.BUDGET_QUAL, runtime.OBSERVER_QUAL,
                runtime.connection.budget.ORIGINAL_PIN, runtime.connection.OBSERVER_PIN):
        a.exact(expected[pin["path"]], pin, "QUALIFICATION_AND_ORIGINALS_INSIDE_FRAME")
    if data["failed_runtime_pin"] is not None:
        a.exact(expected[runtime.FAILED125["path"]], runtime.FAILED125, "FAILED125_PRESERVED_IN_FRAME")
    return row, listing, evidence, proof


def run(root_pin):
    require(type(root_pin) is dict and root_pin.get("path") == root_path(original.r.CONFIG),
            "EXACT_REVIEWED_ROOT")
    pin = original.candidate.ACCEPTOR_PIN
    with (a.c.ROOT / pin["path"]).open("rb") as stream:
        raw = stream.read(pin["bytes"] + 1)
    execute, _ = original.run_projection(raw, root_pin)
    execute.__globals__.update(SELF=SELF, TEST=TEST, runtime=runtime.context(original.r.CONFIG),
        CONTROLLERS=tuple(dict.fromkeys(execute.__globals__["CONTROLLERS"] + CONTROLLERS)),
        prepare=lambda q: prepare(q, root_pin))
    return execute()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=int, required=True)
    parser.add_argument("--root-bytes", type=int, required=True)
    parser.add_argument("--root-sha256", required=True)
    args = parser.parse_args()
    original.r.configure(args.case)
    root = dict(path=root_path(original.r.CONFIG), bytes=args.root_bytes, sha256=args.root_sha256)
    original.r.scope.pins([root])
    raise SystemExit(run(root))
