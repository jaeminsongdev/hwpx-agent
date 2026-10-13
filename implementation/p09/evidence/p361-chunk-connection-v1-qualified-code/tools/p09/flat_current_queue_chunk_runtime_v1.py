"""Fixed opt-in chunk connection, original full runtime and acceptor retained.

One module serves parent/worker/preflight/independent acceptance; no per-case
controller chain. Explicit DATA preserves the failed126 preflight and all prior
DATA/code. All Native two-byte/identity/Job/GO/resource/deadline predicates stay.
"""
import argparse
import json
import re
import sys
from types import FunctionType, SimpleNamespace as NS

import flat_current_queue_budget_runtime_v2 as prior
import flat_current_queue_budget_acceptance_v2 as accepted
import reusable_audit_chunk_v1 as chunk

base = prior.base
a = prior.a
c = prior.c
SELF = "tools/p09/flat_current_queue_chunk_runtime_v1.py"
TEST = "tools/p09/tests/test_flat_current_queue_chunk_connection_v1.py"
FILES = (SELF, TEST, chunk.SELF, chunk.TEST)
CONTROLLERS = tuple(dict.fromkeys(accepted.CONTROLLERS + FILES))
CODE_QUALIFICATION_PATH = "implementation/p09/evidence/p09-361-case126-chunk-connection-code-qualification-r284.v1.json"
QUALIFICATION = dict(path="implementation/p09/evidence/p09-361-case126-stop-and-reusable-chunk-qualification-r282.v1.json",
    bytes=14689, sha256="3a89e24990c8d2c3050fd147cbd05c201ddac35021b596595cf89a1d327d0da5")
FAILED126 = dict(path="implementation/p09/evidence/p09-361-case126-budget-terminal-preflight001.v1.json",
    bytes=42554, sha256="1ba359b53cb573ec5cb3cbb747878afc053a14c8afdb1de1730b9135a30f3507")


def require(ok, code):
    if not ok:
        raise ValueError("CHUNK_CONNECTION_" + code)


def attempt(index):
    require(type(index) is int and 126 <= index <= 249, "INDEX")
    return 1


def data_path(index):
    attempt(index)
    return f"implementation/p09/evidence/p09-361-case{index}-chunk-connection-data001.v1.json"


def validate_data(row, step):
    require(type(row) is dict and set(row) == {"schema_version", "index", "before", "run",
        "base_step_pin", "prior_terminal_data_pin", "failed_preflight_pin",
        "scratch_qualification_pin", "connection_qualification_pin", "connection_code_pins"}, "DATA_SHAPE")
    a.fields(row, dict(schema_version="hwpx-agent.p09-flat-chunk-connection/v1",
        index=step.index, before=step.before, run=attempt(step.index)), "DATA_CURSOR")
    a.exact(row["base_step_pin"], step.pin, "EXACT_BASE_STEP")
    require(set(base.scope.pins([row["prior_terminal_data_pin"]], 1)) == {
        prior.data_path(step.index)}, "EXACT_PRIOR_DATA_PATH")
    a.exact(row["failed_preflight_pin"], FAILED126 if step.index == 126 else None, "REVIEWED_PREFLIGHT_ONLY")
    a.exact(row["scratch_qualification_pin"], QUALIFICATION, "SCRATCH_QUALIFICATION")
    require(set(base.scope.pins([row["connection_qualification_pin"]], 1)) == {
        CODE_QUALIFICATION_PATH}, "EXACT_CODE_QUALIFICATION_PATH")
    require(set(base.scope.pins(row["connection_code_pins"], len(FILES))) == set(FILES), "ALL_FIXED_CHUNK_CODE")
    return row


def connection_data(q):
    require(base.CONFIG is not None, "CONFIG_REQUIRED")
    text = q.text(data_path(base.CONFIG.index))
    require(0 < len(text.encode("utf-8")) <= 16384, "BOUNDED_DATA")
    return validate_data(json.loads(text, object_pairs_hook=base.unique), base.CONFIG)


def own_reviewed_inputs(q, run):
    row = connection_data(q)
    a.exact(run, row["run"], "EXPLICIT_FIRST_PRODUCT_ATTEMPT")
    qualification = a.read_exact(q, QUALIFICATION)
    a.fields(qualification, dict(
        state="PASS_BOUNDED_STOP_REVIEW_AND_CHUNK_CANDIDATE_NOT_WHOLE126_OR_PRODUCT_ACCEPTANCE",
        accepted_count_after=119, accepted_count_delta=0, next_runtime_index=126,
        full126_preflight_retry_executed=False, actual126_product_executed=False,
        PC_freeze_resolved=False), "CANDIDATE_NOT_RUNTIME_ACCEPTANCE")
    small = qualification["candidate_qualification"]
    a.fields(small["synthetic_contracts"], dict(run=15, failures=0, errors=0, skips=0), "SCRATCH15")
    for pin in small["code_pins"] + qualification["preserved_fixed_code_postcheck"]["fixed_code_pins"]:
        a.exact(q.pin(pin["path"]), pin, "PRESERVED_QUALIFIED_CODE")
    for pin in row["connection_code_pins"]:
        a.exact(q.pin(pin["path"]), pin, "ALL_CURRENT_CHUNK_CODE")
    connected = a.read_exact(q, row["connection_qualification_pin"])
    a.fields(connected, dict(state="PASS_CHUNK_CONNECTION14_AND_ORIGINAL_SCRATCH15_NOT_FULL_PREFLIGHT_OR_RUNTIME",
        actual126_product_executed=False, accepted_count_after=119, accepted_count_delta=0,
        Native_source_or_product_runtime_qualified=False, cleanup_confirmed=True), "CONNECTION_QUAL_NOT_PRODUCT")
    a.fields(connected["contracts"], dict(run=29, errors=0, failures=0, skips=0), "CONNECTION29")
    a.exact(connected["new_code_pins"], row["connection_code_pins"], "SAME_TESTED_CONNECTION_CODE")
    a.exact(q.pin(chunk.ORIGINAL_PIN["path"]), chunk.ORIGINAL_PIN, "ORIGINAL_LEAF_PIN")
    if row["failed_preflight_pin"] is not None:
        failed = a.read_exact(q, FAILED126)
        a.fields(failed, dict(state="FAILED_NOT_ACCEPTED",
            error_code="STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME",
            product_worker_or_Native_frame_executed=False, accepted_count_delta=0,
            cleanup_confirmed=True, fresh_inputs=197, fresh_read_passes=266,
            fresh_bytes_read=58309380, final_fresh_hashes=67), "IMMUTABLE_PREBODY_STOP")
        a.fields(failed["metadata_connection"], dict(checks=5028, warning_stops=1,
            latched=True, active=False, original_checkpoint_restored=True,
            complete_source_reads_or_deadlines_weakened=False), "CLOSED_FAILFAST_SCOPE")
    return row


def reviewed_inputs(q, run):
    row = own_reviewed_inputs(q, run)
    prior.reviewed_inputs(q, prior.attempt(base.CONFIG.index))
    a.exact(q.snapshots[prior.data_path(base.CONFIG.index)], row["prior_terminal_data_pin"], "PRIOR_DATA_UNCHANGED")
    return row


def binding_attempt(q, run):
    reviewed_inputs(q, run)
    required, rust = base.binding(q)
    return base.scope.extend(required, q.snapshots), rust


def context(step):
    return NS(**{**vars(prior.context(step)), "SELF": SELF, "TEST": TEST})


def leaf_bytes():
    pin = chunk.ORIGINAL_PIN
    base.stable.stable.prior.build.direct_path(c.ROOT / pin["path"], file_required=True)
    with (c.ROOT / pin["path"]).open("rb") as stream:
        raw = stream.read(pin["bytes"] + 1)
    # Exact hash/size are checked by the original-leaf AST projector itself.
    chunk.project_read(raw)
    return raw


def workspace_report(reader):
    if getattr(reader, chunk.ATTRIBUTE, None) is None:
        return dict(workspace_used=False)
    return dict(workspace_used=True, **chunk.summary(reader))


def connect_engine(engine, raw):
    environment = engine.run_owned.__globals__
    require(environment["SELF"] == SELF and environment["TEST"] == TEST, "EXACT_LOCAL_ENGINE")
    build = environment["build"]
    BuildReader, build_proof = chunk.reader_type(build.BuildReader, raw)
    Boundary, boundary_proof = chunk.reader_type(environment["BoundaryReader"], raw)
    original_summary = build.pressure_summary

    def pressure_summary(guard):
        return dict(original_summary(guard), reusable_chunk_metadata_reader=workspace_report(guard.reader))

    class BoundaryReader(Boundary):
        def diagnostics(self):
            return dict(super().diagnostics(), reusable_chunk_workspace=workspace_report(self))

    environment.update(build=NS(**{**vars(build), "BuildReader": BuildReader,
        "pressure_summary": pressure_summary}), BoundaryReader=BoundaryReader)
    return dict(original_engine_bytecode_unchanged=True,
        original_build_module_and_default_reader_unmodified=True,
        metadata_reader_leaf_projection=build_proof, boundary_reader_leaf_projection=boundary_proof,
        original_identity_pressure_byte_and_open_wrappers_preserved=True,
        added_sampler_thread_or_query=False, runtime_product_connection_qualified=False)


def template():
    environment = dict(vars(prior.metadata), SELF=SELF, TEST=TEST)
    engine, proof = FunctionType(prior.metadata.template.__code__, environment,
        argdefs=prior.metadata.template.__defaults__)()
    proof["reusable_chunk_factory_connection"] = connect_engine(engine, leaf_bytes())
    return engine, proof


def worker(task):
    a.exact(base.run_for(task), attempt(base.CONFIG.index), "EXACT_WORKER_ATTEMPT")
    engine, _ = template()
    return engine.worker(task)


def run_owned(run):
    a.exact(run, attempt(base.CONFIG.index), "EXPLICIT_FIRST_RUN")
    environment = dict(vars(prior.prior), attempt=attempt, template=template, binding_attempt=binding_attempt)
    return FunctionType(prior.prior.run_owned.__code__, environment,
        argdefs=prior.prior.run_owned.__defaults__)(run)


def preflight_projection(raw, leaf):
    unchanged = prior.preflight_projection(raw)
    old = unchanged.__code__
    constants = tuple("-chunk-preflight001.v1.json" if x == "-budget-terminal-preflight001.v1.json"
        else x for x in old.co_consts)
    require(sum(type(x) is str and x == "-budget-terminal-preflight001.v1.json"
        for x in old.co_consts) == 1, "ONE_FRESH_DESTINATION")
    projected = old.replace(co_consts=constants)
    require(projected.replace(co_consts=old.co_consts) == old, "ALL_ORIGINAL_PREFLIGHT_BYTECODE_RETAINED")
    Reader, proof = chunk.reader_type(a.AcceptanceReader, leaf)
    instances = []

    class PreflightReader(Reader):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            require(not instances, "ONE_PREFLIGHT_READER")
            instances.append(self)

    def dump(row, stream, **kw):
        report = workspace_report(instances[0]) if instances else dict(workspace_used=False)
        return json.dump(dict(row, reusable_chunk_preflight_reader=report,
            reusable_chunk_projection_proof=proof), stream, **kw)

    environment = dict(unchanged.__globals__, SELF=SELF, TEST=TEST, template=template,
        connection_data=connection_data, binding_attempt=binding_attempt, data_path=data_path,
        a=NS(**{**vars(a), "AcceptanceReader": PreflightReader}), json=NS(**{**vars(json), "dump": dump}))
    return FunctionType(projected, environment, argdefs=unchanged.__defaults__)


def preflight():
    pin = prior.prior.METADATA_PIN
    base.stable.stable.prior.build.direct_path(c.ROOT / pin["path"], file_required=True)
    with (c.ROOT / pin["path"]).open("rb") as stream:
        raw = stream.read(pin["bytes"] + 1)
    return preflight_projection(raw, leaf_bytes())()


def actual_workspace(diag, passes, size):
    a.fields(diag, dict(workspace_used=True, workspace_allocations=1, workspace_bytes=65536,
        active_lease=False, leases=passes, lease_returns=passes, returned_bytes=size,
        invalid_readinto_returns=0, fresh_stream_read_before_every_exposed_chunk=True,
        unread_tail_exposed=False, file_bytes_or_hash_or_JSON_cache=False,
        original_MRO_wrappers_preserved=True, original_stream_open_and_identity_binding_preserved=True,
        original_checkpoints_pacing_parse_budget_and_final_hashes_preserved=True,
        added_sampler_query_thread_or_process=False, PC_freeze_resolved=False), "ACTUAL_WORKSPACE")
    require(type(diag["readinto_attempts"]) is int and diag["readinto_attempts"] >= passes,
        "ACTUAL_READINTO_NOT_IMPORT_ONLY")
    a.exact(diag["readinto_completed"], diag["readinto_attempts"], "ALL_READINTO_COMPLETED")


def actual_chunk_binding(row):
    metadata = row["bootstrap_metadata"]
    actual_workspace(metadata["early_pressure"]["reusable_chunk_metadata_reader"],
        metadata["read_passes"], metadata["bytes_read"])
    boundaries = row["source_frame"]["actual_byte_boundaries"]
    require(type(boundaries) is list and len(boundaries) == 2, "TWO_WHOLE_BOUNDARIES")
    for boundary in boundaries:
        diag = boundary["reader_diagnostics"]
        actual_workspace(diag["reusable_chunk_workspace"], diag["read_passes"], diag["bytes_read"])
    return True


def validator(raw, ctx, flat=True):
    project, proof = accepted.validator(raw, ctx, flat)
    project.__globals__["CONTROLLERS"] = tuple(dict.fromkeys(
        project.__globals__["CONTROLLERS"] + FILES))
    return project, dict(proof, reusable_chunk_controller_pins_added=True)


def validate_candidate(q, row, listing, oldbody, fresh, ctx, flat=True):
    # Same complete v2 terminal/full/metadata/early-budget oracle, not a fixture
    # compatibility validator. Actual scratch usage is ADDITIONAL proof.
    environment = dict(accepted.validate_candidate.__globals__, validator=validator)
    evidence, proof = FunctionType(accepted.validate_candidate.__code__, environment,
        argdefs=accepted.validate_candidate.__defaults__)(q, row, listing, oldbody, fresh, ctx, flat)
    actual_chunk_binding(row)
    proof["actual_metadata_and_two_whole_boundary_chunk_usage_checked"] = True
    return evidence, proof


def root_path(step):
    return f"implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run{attempt(step.index):03}.v1.json"


def prepare_projection(raw):
    environment = dict(accepted.prior.metadata.prepare_projection.__globals__,
        root_path=root_path, validate_candidate=validate_candidate, runtime=NS(context=context))
    return FunctionType(accepted.prior.metadata.prepare_projection.__code__, environment,
        argdefs=accepted.prior.metadata.prepare_projection.__defaults__)(raw)


def prepare(q, root_pin):
    data = own_reviewed_inputs(q, attempt(base.CONFIG.index))
    environment = dict(accepted.prepare.__globals__, prepare_projection=prepare_projection)
    row, listing, evidence, proof = FunctionType(accepted.prepare.__code__, environment,
        argdefs=accepted.prepare.__defaults__)(q, root_pin)
    a.exact(q.snapshots[prior.data_path(base.CONFIG.index)], data["prior_terminal_data_pin"],
        "ACCEPT_PRIOR_TERMINAL_DATA_UNCHANGED")
    expected = base.scope.pins(row["source_freeze"])
    for pin in data["connection_code_pins"] + [QUALIFICATION, chunk.ORIGINAL_PIN, data["connection_qualification_pin"]]:
        a.exact(expected[pin["path"]], pin, "CHUNK_CODE_AND_QUAL_INSIDE_NATIVE_FRAME")
    for name in (data_path(base.CONFIG.index), prior.data_path(base.CONFIG.index)):
        a.exact(expected[name], q.snapshots[name], "CHUNK_AND_PRIOR_DATA_INSIDE_FRAME")
    if data["failed_preflight_pin"] is not None:
        a.exact(expected[FAILED126["path"]], FAILED126, "FAILED126_PRESERVED_INSIDE_FRAME")
    return row, listing, evidence, proof


def accept(root_pin):
    require(type(root_pin) is dict and root_pin.get("path") == root_path(base.CONFIG), "EXACT_CANONICAL_ROOT")
    pin = accepted.original.candidate.ACCEPTOR_PIN
    with (c.ROOT / pin["path"]).open("rb") as stream:
        raw = stream.read(pin["bytes"] + 1)
    execute, _ = accepted.original.run_projection(raw, root_pin)
    execute.__globals__.update(SELF=SELF, TEST=TEST, runtime=context(base.CONFIG),
        CONTROLLERS=tuple(dict.fromkeys(execute.__globals__["CONTROLLERS"] + CONTROLLERS)),
        prepare=lambda q: prepare(q, root_pin))
    return execute()


if __name__ == "__main__":
    try:
        if len(sys.argv) == 4 and sys.argv[1:3] == ["--owned-worker", "--task"]:
            base.configure(base.task_index(sys.argv[3]))
            raise SystemExit(worker(sys.argv[3]))
        parser = argparse.ArgumentParser()
        parser.add_argument("--case", type=int, required=True)
        parser.add_argument("--run", type=int)
        parser.add_argument("--preflight", action="store_true")
        parser.add_argument("--accept", action="store_true")
        parser.add_argument("--root-bytes", type=int)
        parser.add_argument("--root-sha256")
        args = parser.parse_args()
        base.configure(args.case)
        require(sum((args.run is not None, args.preflight, args.accept)) == 1, "ONE_EXECUTION_MODE")
        if args.accept:
            pin = dict(path=root_path(base.CONFIG), bytes=args.root_bytes, sha256=args.root_sha256)
            base.scope.pins([pin], 1)
            raise SystemExit(accept(pin))
        require(args.root_bytes is None and args.root_sha256 is None, "ACCEPT_ARGUMENTS_ONLY")
        raise SystemExit(preflight() if args.preflight else run_owned(args.run))
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        code = str(exc) if isinstance(exc, ValueError) else "REDACTED_CHUNK_CONNECTION_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED", error_code=code
            if re.fullmatch("[A-Z0-9_]{1,256}", code) else "REDACTED_CHUNK_CONNECTION_FAILURE")))
        raise SystemExit(2) from None
