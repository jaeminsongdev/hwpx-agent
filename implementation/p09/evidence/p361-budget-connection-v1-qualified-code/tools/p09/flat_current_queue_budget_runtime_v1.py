"""Explicit per-step DATA connects early PDH budget to the sole original observer.

Reviewed125/run002 only; later steps first001, no automatic retry. All original
metadata/full-source/Native two-byte/GO/Job/resource/cleanup predicates retained.
No qualified source edits, larger deadline, source omission or queue writes.
"""
import argparse
import ast
import copy
import hashlib
import json
import re
import sys
from types import FunctionType, SimpleNamespace as NS

import flat_current_queue_metadata_runtime as metadata
import serial_observer_budget_connection_v1 as connection

base = metadata.base
a = metadata.a
c = metadata.c
SELF = "tools/p09/flat_current_queue_budget_runtime_v1.py"
TEST = "tools/p09/tests/test_flat_current_queue_budget_connection_v1.py"
ACCEPTOR = "tools/p09/flat_current_queue_budget_acceptance_v1.py"
FILES = (SELF, TEST, ACCEPTOR, connection.SELF, connection.TEST,
         connection.budget.SELF, connection.budget.TEST)
FAILED125 = dict(path="implementation/p09/evidence/p09-361-case125-current-runtime-run001.v1.json",
    bytes=411802, sha256="a23992d43df24d545cf75dcb47ed5560ee5da099d238481ccbe881c4ae86e4a0")
BUDGET_QUAL = dict(path="implementation/p09/evidence/p09-361-case125-native-stop-and-budget-qualification-r272.v1.json",
    bytes=23335, sha256="b05773f353b4877c3902314f785f4cbd70d0db3194ec71c1cfef1e9bfde37c4d")
OBSERVER_QUAL = dict(path="implementation/p09/evidence/p09-361-case125-observer-budget-connection-qualification-r273.v1.json",
    bytes=17287, sha256="44650363a1895edd072d709ab9bc50c4e78551f0a9bf7cff5be03982d59bb8bd")
METADATA_PIN = dict(path=metadata.SELF, bytes=13283,
    sha256="cc8fa8950e252e19ff58ad682ab01dba3fe0b0a82b5f4b2f3324072089bc0bf0")


def require(ok, code):
    if not ok:
        raise ValueError("BUDGET_CONNECTION_" + code)


def attempt(index):
    require(type(index) is int and 125 <= index <= 249, "INDEX")
    return 2 if index == 125 else 1


def data_path(index):
    attempt(index)
    return f"implementation/p09/evidence/p09-361-case{index}-budget-connection-data001.v1.json"


def validate_data(row, step):
    require(type(row) is dict and set(row) == {
        "schema_version", "index", "before", "run", "base_step_pin",
        "metadata_connection_pin", "failed_runtime_pin", "budget_qualification_pin",
        "observer_qualification_pin", "connection_code_pins"}, "DATA_SHAPE")
    a.fields(row, dict(schema_version="hwpx-agent.p09-flat-budget-connection/v1",
        index=step.index, before=step.before, run=attempt(step.index)), "DATA_CURSOR")
    a.exact(row["base_step_pin"], step.pin, "UNCHANGED_STEP")
    pins = base.scope.pins([row["metadata_connection_pin"]], 1)
    require(set(pins) == {metadata.data_path(step.index)}, "UNCHANGED_METADATA_DATA_PATH")
    a.exact(row["failed_runtime_pin"], FAILED125 if step.index == 125 else None, "REVIEWED_RETRY_ONLY")
    a.exact(row["budget_qualification_pin"], BUDGET_QUAL, "QUALIFIED_BUDGET")
    a.exact(row["observer_qualification_pin"], OBSERVER_QUAL, "QUALIFIED_OBSERVER")
    require(set(base.scope.pins(row["connection_code_pins"], len(FILES))) == set(FILES), "ALL_NEW_CODE")
    return row


def connection_data(q):
    step = base.CONFIG
    require(step is not None, "CONFIG_REQUIRED")
    text = q.text(data_path(step.index))
    require(0 < len(text.encode("utf-8")) <= 16384, "BOUNDED_DATA")
    return validate_data(json.loads(text, object_pairs_hook=base.unique), step)


def review_failure(row):
    a.fields(row, dict(state="DEFERRED_NOT_STARTED", selected_test_index=125,
        stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION", worker_created=False,
        product_body_observed=False, Native_source_frame_qualified=False,
        cleanup_confirmed=True, owned_tree_empty=True, accepted_count_delta=0,
        full249_current_qualified=False, signed16_current_qualified=False,
        P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN"), "EXACT_PREBODY_FAILURE")
    a.exact(row["passed_test_names"], [], "NO_BODY_REPLAY")
    a.exact(row["source_freeze"], [], "NO_COMMITTED_FRAME_FROM_FAILURE")
    frame = row["source_frame"]
    a.fields(frame, dict(frame_state="CLOSED"), "FAILED_FRAME_CLOSED")
    a.exact(frame["actual_byte_boundaries"], [], "NO_COMPLETED_BYTES")
    a.fields(frame["handles"], dict(input_lock_handles_opened=2178,
        input_lock_handles_closed=2178, input_lock_handles_remaining=0,
        input_lock_cleanup_confirmed=True, handle_close_failed_attempts=0,
        active_reader_bindings=0, active_byte_streams=0, byte_stream_identity_checks=0), "ALL_FAILED_HANDLES_CLOSED")
    return True


def read_raw(q, pin):
    actual, buffer = q._read(pin["path"], parse=True)
    q._bind(pin["path"], actual)
    a.exact(actual, pin, "FROZEN_RAW_SOURCE")
    return bytes(buffer)


def reviewed_inputs(q, run):
    row = connection_data(q)
    a.exact(run, row["run"], "EXACT_AUTHORIZED_ATTEMPT")
    # Preserve original metadata DATA, code4 and qualification checks. This is
    # NOT calling or bypassing metadata.run_owned(2), which refuses125/run002.
    metadata.reviewed_inputs(q, 1)
    a.exact(q.snapshots[metadata.data_path(base.CONFIG.index)],
            row["metadata_connection_pin"], "OLD_METADATA_DATA_UNCHANGED")
    qual = a.read_exact(q, BUDGET_QUAL)
    a.fields(qual, dict(state="PASS_REVIEWED_FAILED125_AND_SYNTHETIC11_NOT_RUNTIME_CONNECTION_OR_GATE",
        runtime_connection_qualified=False), "SYNTHETIC_BUDGET_NOT_PRODUCT")
    observed = a.read_exact(q, OBSERVER_QUAL)
    a.fields(observed, dict(state="PASS_SYNTHETIC20_AND_REAL_SOLE_OBSERVER_NOT_PRODUCT_RUNTIME_OR_RETRY",
        synthetic_contracts_passed=20, runtime_product_connection_qualified=False,
        reviewed_retry_run002_executed=False, accepted_count_after=118,
        accepted_count_delta=0), "LIGHT_OBSERVER_NOT_PRODUCT")
    live = observed["actual_sole_observer_qualification"]
    a.fields(live, dict(actual_PDH_probe=True, worker_or_Native_input_frame_executed=False,
        observer_cleanup=True, guard_cleanup=True, original_windows_class_restored=True),
        "REAL_SOLE_OBSERVER_CLEANED")
    binding = live["after_close_summary"]["early_budget_probe_connection"]
    a.fields(binding, dict(existing_observer_instances=1, budget_probe_instances=1,
        instance_binding_observed=True, additional_PDH_query=False,
        second_sampler_thread_or_process=False), "REAL_FACTORY_BINDING")
    for pin in observed["synthetic_qualification"]["code_pins"]:
        a.exact(q.pin(pin["path"]), pin, "PRESERVED_QUALIFIED_BUDGET_AND_CONNECTION")
    for pin in row["connection_code_pins"]:
        a.exact(q.pin(pin["path"]), pin, "ALL_CONNECTION_CODE_CURRENT")
    a.exact(q.pin(connection.OBSERVER_PIN["path"]), connection.OBSERVER_PIN, "ORIGINAL_OBSERVER_BYTES")
    read_raw(q, connection.budget.ORIGINAL_PIN)
    if row["failed_runtime_pin"] is not None:
        review_failure(a.read_exact(q, row["failed_runtime_pin"]))
    return row


def binding_attempt(q, run):
    reviewed_inputs(q, run)
    required, rust = base.binding(q)
    return base.scope.extend(required, q.snapshots), rust


def context(step):
    return NS(**{**vars(metadata.context(step)), "SELF": SELF, "TEST": TEST})


def template():
    # Identical qualified metadata factory bytecode; only command metadata of
    # this explicitly pinned controller differs. Original build module intact.
    env = dict(vars(metadata), SELF=SELF, TEST=TEST)
    project = FunctionType(metadata.template.__code__, env,
                           argdefs=metadata.template.__defaults__)
    return project()


def worker(task):
    import flat_current_queue_budget_acceptance_v1
    a.exact(base.run_for(task), attempt(base.CONFIG.index), "WORKER_ATTEMPT")
    engine, _ = template()
    return engine.worker(task)


def run_owned(run):
    import flat_current_queue_budget_acceptance_v1
    a.exact(run, attempt(base.CONFIG.index), "PARENT_ATTEMPT")
    api, _ = base.entry()
    api.run_owned.__globals__.update(template=template, binding_attempt=binding_attempt)
    pin = connection.budget.ORIGINAL_PIN
    base.stable.stable.prior.build.direct_path(c.ROOT / pin["path"], file_required=True)
    with (c.ROOT / pin["path"]).open("rb") as stream:
        raw = stream.read(pin["bytes"] + 1)
    connection.bind_entry(api, raw)
    return api.run_owned(run)


def preflight_projection(raw):
    require(type(raw) is bytes and len(raw) == METADATA_PIN["bytes"]
        and hashlib.sha256(raw).hexdigest() == METADATA_PIN["sha256"], "EXACT_PREFLIGHT_SOURCE")
    nodes = [n for n in ast.parse(raw.decode("utf-8")).body
             if isinstance(n, ast.FunctionDef) and n.name == "preflight"]
    require(len(nodes) == 1, "ONE_ORIGINAL_PREFLIGHT")
    node = copy.deepcopy(nodes[0])
    before = ast.dump(node, include_attributes=False)
    changes = 0
    class Project(ast.NodeTransformer):
        def visit_Constant(self, n):
            nonlocal changes
            if n.value == "-metadata-preflight001.v1.json":
                changes += 1
                updated = ast.Constant("-budget-preflight001.v1.json")
                updated._original_destination = copy.deepcopy(n)
                return updated
            return n
    node = Project().visit(node)
    require(changes == 1, "ONE_FRESH_OUTPUT_METADATA_CHANGE")
    class Undo(ast.NodeTransformer):
        def visit(self, n):
            if hasattr(n, "_original_destination"):
                return copy.deepcopy(n._original_destination)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)), include_attributes=False) == before,
            "ALL_ORIGINAL_PREFLIGHT_STATEMENTS_RETAINED")
    env = dict(vars(metadata), SELF=SELF, TEST=TEST, template=template,
        connection_data=connection_data, binding_attempt=binding_attempt, data_path=data_path)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 METADATA_PIN["path"], "exec"), env)
    return env["preflight"]


def preflight():
    import flat_current_queue_budget_acceptance_v1
    base.stable.stable.prior.build.direct_path(c.ROOT / METADATA_PIN["path"], file_required=True)
    with (c.ROOT / METADATA_PIN["path"]).open("rb") as stream:
        raw = stream.read(METADATA_PIN["bytes"] + 1)
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
        code = str(exc) if isinstance(exc, ValueError) else "REDACTED_BUDGET_CONNECTION_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED", error_code=code
            if re.fullmatch("[A-Z0-9_]{1,256}", code) else "REDACTED_BUDGET_CONNECTION_FAILURE")))
        raise SystemExit(2) from None
