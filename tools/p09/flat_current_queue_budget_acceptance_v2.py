"""Full original oracle + actual early-budget + terminal admission connection.

Only canonical reviewed125/run003/later001 roots. Explicit DATA/code/failure/
qualification pins inside whole Native scope; no prebody/synthetic acceptance.
"""
import argparse
from types import FunctionType

import flat_current_queue_budget_acceptance_v1 as prior
import flat_current_queue_budget_runtime_v2 as runtime

original = prior.original
a = prior.a
SELF = runtime.ACCEPTOR
TEST = runtime.TEST
CONTROLLERS = tuple(dict.fromkeys(prior.CONTROLLERS + runtime.FILES))


def root_path(step):
    return f"implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run{runtime.attempt(step.index):03}.v1.json"


def validator(raw, ctx, flat=True):
    project, proof = prior.validator(raw, ctx, flat)
    project.__globals__["CONTROLLERS"] = tuple(dict.fromkeys(
        project.__globals__["CONTROLLERS"] + CONTROLLERS))
    return project, dict(proof, terminal_admission_controller_pins_added=True)


def validate_candidate(q, row, listing, oldbody, fresh, ctx, flat=True):
    runtime.terminal.require_completed_body(row)
    environment = dict(prior.validate_candidate.__globals__, validator=validator)
    unchanged = FunctionType(prior.validate_candidate.__code__, environment,
                             argdefs=prior.validate_candidate.__defaults__)
    evidence, proof = unchanged(q, row, listing, oldbody, fresh, ctx, flat)
    proof["actual_completed_body_admission_before_capture_access"] = True
    return evidence, proof


def prepare_projection(raw):
    environment = dict(prior.metadata.prepare_projection.__globals__,
        root_path=root_path, validate_candidate=validate_candidate, runtime=runtime)
    unchanged = FunctionType(prior.metadata.prepare_projection.__code__, environment,
                             argdefs=prior.metadata.prepare_projection.__defaults__)
    return unchanged(raw)


def prepare(q, root_pin):
    data = runtime.reviewed_inputs(q, runtime.attempt(original.r.CONFIG.index))
    source = q.text(original.SELF).encode("utf-8")
    qualification = a.read_exact(q, runtime.metadata.QUALIFIED)
    pins = {p["path"]: p for p in qualification["frozen_core_pins"]}
    a.exact(q.snapshots[original.SELF], pins[original.SELF], "TERMINAL_FROZEN_FLAT_ACCEPTOR")
    row, listing, evidence, proof = prepare_projection(source)(q, root_pin)
    expected = original.r.scope.pins(row["source_freeze"])
    for pin in data["connection_code_pins"]:
        a.exact(expected[pin["path"]], pin, "TERMINAL_ALL_CODE_IN_NATIVE_FRAME")
    for name in (runtime.data_path(original.r.CONFIG.index),
                 runtime.prior.data_path(original.r.CONFIG.index),
                 runtime.metadata.data_path(original.r.CONFIG.index)):
        a.exact(expected[name], q.snapshots[name], "TERMINAL_ALL_DATA_INSIDE_FRAME")
    for pin in (runtime.BUDGET_QUAL, runtime.OBSERVER_QUAL, runtime.TERMINAL_QUAL,
                runtime.connection.budget.ORIGINAL_PIN, runtime.connection.OBSERVER_PIN):
        a.exact(expected[pin["path"]], pin, "TERMINAL_QUAL_AND_ORIGINALS_INSIDE_FRAME")
    for pin in data["failed_runtime_pins"]:
        a.exact(expected[pin["path"]], pin, "TERMINAL_FAILURES_PRESERVED_IN_FRAME")
    return row, listing, evidence, proof


def run(root_pin):
    prior.require(type(root_pin) is dict and root_pin.get("path") == root_path(original.r.CONFIG),
                  "EXACT_TERMINAL_REVIEWED_ROOT")
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
