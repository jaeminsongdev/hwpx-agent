"""Fixed terminal-admission connection and explicit reviewed125/run003 DATA.

Preserve v1 DATA/code, both prebody failures, full source/Native byte/rate/
deadline/GO/Job/sole-observer guards. No automatic retries or queue writes.
"""
import argparse
import ast
import copy
import hashlib
import json
import re
import sys
from types import FunctionType, SimpleNamespace as NS

import flat_current_queue_budget_runtime_v1 as prior
import flat_candidate_terminal_review_guard_v1 as terminal

base = prior.base
metadata = prior.metadata
connection = prior.connection
a = prior.a
c = prior.c
SELF = "tools/p09/flat_current_queue_budget_runtime_v2.py"
TEST = "tools/p09/tests/test_flat_current_queue_budget_connection_v2.py"
ACCEPTOR = "tools/p09/flat_current_queue_budget_acceptance_v2.py"
FILES = (SELF, TEST, ACCEPTOR, terminal.SELF, terminal.TEST) + prior.FILES
BUDGET_QUAL = prior.BUDGET_QUAL
OBSERVER_QUAL = prior.OBSERVER_QUAL
FAILED125 = prior.FAILED125
FAILED002 = dict(path="implementation/p09/evidence/p09-361-case125-current-runtime-run002.v1.json",
    bytes=263480, sha256="33990111d0b79fa568d58d7c9f898b3ed2541e280c8e4ca4b2957da5f9e262ad")
TERMINAL_QUAL = dict(path="implementation/p09/evidence/p09-361-case125-terminal-review-guard-and-fresh-postcheck-r276.v1.json",
    bytes=4318, sha256="ba30a295c3ddd67e13e335b74698407ff0b2d491e904a35858b07b17339b5502")


def require(ok, code):
    if not ok:
        raise ValueError("TERMINAL_CONNECTION_" + code)


def attempt(index):
    prior.attempt(index)
    return 3 if index == 125 else 1


def data_path(index):
    attempt(index)
    return f"implementation/p09/evidence/p09-361-case{index}-budget-terminal-connection-data001.v1.json"


def validate_data(row, step):
    require(type(row) is dict and set(row) == {"schema_version", "index", "before", "run",
        "base_step_pin", "prior_budget_connection_pin", "failed_runtime_pins",
        "terminal_qualification_pin", "connection_code_pins"}, "DATA_SHAPE")
    a.fields(row, dict(schema_version="hwpx-agent.p09-flat-budget-terminal-connection/v2",
        index=step.index, before=step.before, run=attempt(step.index)), "DATA_CURSOR")
    a.exact(row["base_step_pin"], step.pin, "EXACT_STEP")
    require(set(base.scope.pins([row["prior_budget_connection_pin"]], 1)) == {
        prior.data_path(step.index)}, "PRIOR_DATA_PATH")
    a.exact(row["failed_runtime_pins"], [FAILED125, FAILED002] if step.index == 125 else [],
            "BOTH_REVIEWED_FAILURES_NOT_REPLAY")
    a.exact(row["terminal_qualification_pin"], TERMINAL_QUAL, "TERMINAL_QUALIFICATION")
    require(set(base.scope.pins(row["connection_code_pins"], len(FILES))) == set(FILES), "ALL_FIXED_CODE")
    return row


def connection_data(q):
    require(base.CONFIG is not None, "CONFIG_REQUIRED")
    text = q.text(data_path(base.CONFIG.index))
    require(0 < len(text.encode("utf-8")) <= 16384, "BOUNDED_DATA")
    return validate_data(json.loads(text, object_pairs_hook=base.unique), base.CONFIG)


def review_second_failure(row):
    a.fields(row, dict(state="DEFERRED_NOT_STARTED", selected_test_index=125,
        stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION", worker_created=False,
        product_body_observed=False, Native_source_frame_qualified=False,
        current_generation_runtime_candidate_qualified=False,
        cleanup_confirmed=True, owned_tree_empty=True, accepted_count_delta=0,
        full249_current_qualified=False, signed16_current_qualified=False,
        P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN"), "FAILED002_PREBODY_ONLY")
    a.exact(row["source_freeze"], [], "NO_FAILED_COMMITTED_FREEZE")
    a.exact(row["passed_test_names"], [], "NO_PRODUCT_REPLAY")
    frame = row["source_frame"]
    a.fields(frame, dict(frame_state="CLOSED", registered_live_frame=False), "FAILED002_FRAME_CLOSED")
    a.exact(frame["actual_byte_boundaries"], [], "NO_FAILED_BYTE_PASSES")
    a.fields(frame["handles"], dict(input_lock_handles_opened=1020,
        input_lock_handles_closed=1020, input_lock_handles_remaining=0,
        input_lock_cleanup_confirmed=True, handle_close_failed_attempts=0,
        active_reader_bindings=0, active_byte_streams=0, byte_stream_identity_checks=0), "FAILED002_NO_LEAKS")
    # Actual connected probe evidence, not acceptance of the prebody product.
    attribution = row["serial_CPU_attribution"]
    a.fields(attribution["early_budget_probe_connection"], dict(
        existing_observer_instances=1, budget_probe_instances=1,
        instance_binding_observed=True, additional_PDH_query=False,
        second_sampler_thread_or_process=False, original_K32_decisions_replaced=False),
        "FAILED002_ORIGINAL_SOLE_OBSERVER")
    a.fields(attribution["probes"][0], dict(query_remaining=False, cleanup_confirmed=True,
        early_budget_checks=113, early_budget_stops=1), "FAILED002_QUERY_CLOSED")
    return True


def reviewed_inputs(q, run):
    row = connection_data(q)
    a.exact(run, row["run"], "ONLY_EXPLICIT_REVIEWED_ATTEMPT")
    old = prior.reviewed_inputs(q, prior.attempt(base.CONFIG.index))
    a.exact(q.snapshots[prior.data_path(base.CONFIG.index)], row["prior_budget_connection_pin"],
            "PRIOR_DATA_NOT_REWRITTEN")
    qualification = a.read_exact(q, TERMINAL_QUAL)
    a.fields(qualification, dict(
        state="PASS_TERMINAL_REVIEW8_AND_ACTUAL_FAILED002_EARLY_REJECTION_NOT_PRODUCT_CONNECTION_OR_ACCEPTANCE",
        accepted_count_after=118, accepted_count_delta=0, reviewed_run003_authorized=False,
        reviewed_run003_executed=False, P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN"),
        "REVIEW_QUALIFICATION_NOT_RUNTIME_OR_RETRY")
    for pin in qualification["synthetic_qualification"]["code_pins"]:
        a.exact(q.pin(pin["path"]), pin, "QUALIFIED_TERMINAL_SOURCE")
    for pin in row["connection_code_pins"]:
        a.exact(q.pin(pin["path"]), pin, "CURRENT_FIXED_CONNECTION_CODE")
    if base.CONFIG.index == 125:
        prior.review_failure(a.read_exact(q, FAILED125))
        review_second_failure(a.read_exact(q, FAILED002))
    return row


def binding_attempt(q, run):
    reviewed_inputs(q, run)
    required, rust = base.binding(q)
    return base.scope.extend(required, q.snapshots), rust


def context(step):
    return NS(**{**vars(prior.context(step)), "SELF": SELF, "TEST": TEST})


def template():
    # Identical original metadata template bytecode; command metadata only.
    environment = dict(vars(metadata), SELF=SELF, TEST=TEST)
    return FunctionType(metadata.template.__code__, environment,
                        argdefs=metadata.template.__defaults__)()


def worker(task):
    import flat_current_queue_budget_acceptance_v2
    a.exact(base.run_for(task), attempt(base.CONFIG.index), "EXACT_WORKER_ATTEMPT")
    engine, _ = template()
    return engine.worker(task)


def run_owned(run):
    import flat_current_queue_budget_acceptance_v2
    # Original v1 function bytecode and local single-observer binding retained.
    # Only reviewed attempt/template/binding dependencies of this new DATA differ.
    environment = dict(vars(prior), attempt=attempt, template=template,
                       binding_attempt=binding_attempt)
    return FunctionType(prior.run_owned.__code__, environment,
                        argdefs=prior.run_owned.__defaults__)(run)


def preflight_projection(raw):
    pin = prior.METADATA_PIN
    require(type(raw) is bytes and len(raw) == pin["bytes"] and
        hashlib.sha256(raw).hexdigest() == pin["sha256"], "FROZEN_PREFLIGHT_SOURCE")
    nodes = [n for n in ast.parse(raw.decode("utf-8")).body
             if isinstance(n, ast.FunctionDef) and n.name == "preflight"]
    require(len(nodes) == 1, "ONE_PREFLIGHT")
    node = copy.deepcopy(nodes[0]); before = ast.dump(node, include_attributes=False)
    changes = 0
    class Project(ast.NodeTransformer):
        def visit_Constant(self, n):
            nonlocal changes
            if n.value == "-metadata-preflight001.v1.json":
                changes += 1
                new = ast.Constant("-budget-terminal-preflight001.v1.json")
                new._original_destination = copy.deepcopy(n)
                return new
            return n
    node = Project().visit(node)
    require(changes == 1, "ONE_FRESH_PREFLIGHT_METADATA_CHANGE")
    class Undo(ast.NodeTransformer):
        def visit(self, n):
            if hasattr(n, "_original_destination"):
                return copy.deepcopy(n._original_destination)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)), include_attributes=False) == before,
            "ALL_ORIGINAL_PREFLIGHT_STATEMENTS_RETAINED")
    environment = dict(vars(metadata), SELF=SELF, TEST=TEST, template=template,
        connection_data=connection_data, binding_attempt=binding_attempt, data_path=data_path)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 pin["path"], "exec"), environment)
    return environment["preflight"]


def preflight():
    import flat_current_queue_budget_acceptance_v2
    pin = prior.METADATA_PIN
    base.stable.stable.prior.build.direct_path(c.ROOT / pin["path"], file_required=True)
    with (c.ROOT / pin["path"]).open("rb") as stream:
        raw = stream.read(pin["bytes"] + 1)
    return preflight_projection(raw)()


if __name__ == "__main__":
    try:
        if len(sys.argv) == 4 and sys.argv[1:3] == ["--owned-worker", "--task"]:
            base.configure(base.task_index(sys.argv[3]))
            raise SystemExit(worker(sys.argv[3]))
        parser = argparse.ArgumentParser()
        parser.add_argument("--case", type=int, required=True)
        parser.add_argument("--run", type=int)
        parser.add_argument("--preflight", action="store_true")
        args = parser.parse_args()
        base.configure(args.case)
        require(args.preflight != (args.run is not None), "ONE_MODE")
        raise SystemExit(preflight() if args.preflight else run_owned(args.run))
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        code = str(exc) if isinstance(exc, ValueError) else "REDACTED_TERMINAL_CONNECTION_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED", error_code=code
            if re.fullmatch("[A-Z0-9_]{1,256}", code) else "REDACTED_TERMINAL_CONNECTION_FAILURE")))
        raise SystemExit(2) from None
