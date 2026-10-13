"""Fixed metadata-only source-stat connection; full original runtime retained.

Explicit DATA preserves v1 code/DATA/failed preflight; reviewed127/run002 only.
Ancestor link pairs use one fresh Windows stat with exact-original fallback.
Later cases use run001. No retry loop, source/read cache, guard relaxation or
replacement of the held-Native path adapter. Prior qualified code is untouched.
"""
import argparse
import ast
import copy
import hashlib
import os
import stat
from pathlib import Path
import json
import re
import sys
from types import FunctionType, SimpleNamespace as NS

import flat_current_queue_chunk_runtime_v1 as prior
import single_snapshot_source_guard_v1 as snapshot

base = prior.base
a = prior.a
c = prior.c
SELF = "tools/p09/flat_current_queue_source_stat_runtime_v2.py"
TEST = "tools/p09/tests/test_flat_current_queue_source_stat_connection_v2.py"
FILES = (SELF, TEST, snapshot.SELF, snapshot.TEST)
CONTROLLERS = tuple(dict.fromkeys(prior.CONTROLLERS + FILES))
QUALIFICATION_PATH = "implementation/p09/evidence/p09-361-case127-stop-and-source-stat-qualification-r289.v1.json"
CODE_QUALIFICATION_PATH = "implementation/p09/evidence/p09-361-case127-source-stat-ancestor-connection-code-qualification-r294.v1.json"
FAILED127 = dict(path="implementation/p09/evidence/p09-361-case127-current-runtime-run001.v1.json",
    bytes=46330, sha256="a3b82010ab9bb2b3c486d4db3d4782483ae8d969485f3e16a7d4fa6c42c36cbc")

PRIOR_SOURCE_FILES = ("tools/p09/flat_current_queue_source_stat_runtime_v1.py",
    "tools/p09/tests/test_flat_current_queue_source_stat_connection_v1.py", snapshot.SELF, snapshot.TEST)
PRIOR_CONNECTION_QUAL = dict(path="implementation/p09/evidence/p09-361-case127-source-stat-connection-code-qualification-r290.v1.json",
    bytes=9074, sha256="52513240272662053058f9b7b60793fbd108cdf73fbf6ec29f2eb52ca10627cf")
FAILED_PREFLIGHT = dict(path="implementation/p09/evidence/p09-361-case127-source-stat-preflight001.v1.json",
    bytes=59614, sha256="9b2b0acc4bd09cc239408eb9943f44ebd4e0dfd917839fe084ecec65d65aa866")
ORIGINAL_BUILD_PIN = dict(path="tools/p09/build_case112_current_stored.py",
    bytes=24527, sha256="366f35c2ec22fee9e2b5344402cd2ae79eb9bbc8e3c021e769024ffccd765faa")


def prior_source_data_path(index):
    return f"implementation/p09/evidence/p09-361-case{index}-source-stat-connection-data001.v1.json"


def review_prior_source(q, row):
    connected = a.read_exact(q, PRIOR_CONNECTION_QUAL)
    a.fields(connected, dict(state="PASS_SOURCE_STAT_CONNECTION16_AND_SOURCE10_NOT_FULL_PREFLIGHT_OR_RUNTIME",
        actual127_product_executed=False, accepted_count_after=120, accepted_count_delta=0,
        cleanup_confirmed=True, Native_or_product_runtime_qualified=False), "PRIOR_SOURCE_QUAL")
    a.fields(connected["contracts"], dict(run=26, errors=0, failures=0, skips=0), "PRIOR_SOURCE26")
    a.exact(connected["new_code_pins"], row["prior_source_code_pins"], "PRIOR_SOURCE_CODE_LIST")
    for pin in row["prior_source_code_pins"]:
        a.exact(q.pin(pin["path"]), pin, "PRIOR_SOURCE_UNCHANGED")
    if row["prior_source_data_pin"] is not None:
        data = a.read_exact(q, row["prior_source_data_pin"])
        source = q.text(PRIOR_SOURCE_FILES[0])
        environment = dict(base=base, a=a, prior=prior, snapshot=snapshot,
            QUALIFICATION_PATH=QUALIFICATION_PATH, CODE_QUALIFICATION_PATH=PRIOR_CONNECTION_QUAL["path"],
            FILES=PRIOR_SOURCE_FILES, FAILED127=FAILED127)
        # Compile only the exact original validation definitions; no import of
        # another runtime/controller or loss of its DATA predicates.
        old = base.native.definitions(source,
            ("require", "attempt", "data_path", "validate_data"), environment)
        old.validate_data(data, base.CONFIG)
        a.exact(data["connection_code_pins"], row["prior_source_code_pins"], "PRIOR_DATA_SOURCE_BYTES")
        a.exact(data["connection_qualification_pin"], PRIOR_CONNECTION_QUAL, "PRIOR_DATA_QUAL")
        failed = a.read_exact(q, FAILED_PREFLIGHT)
        a.fields(failed, dict(state="FAILED_NOT_ACCEPTED",
            error_code="STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME", cleanup_confirmed=True,
            product_worker_or_Native_frame_executed=False, accepted_count_delta=0), "FAILED_PREFLIGHT_NOT_ACCEPTED")
        a.exact(failed["final_fresh_hashes"], 152, "PRESERVED_PARTIAL_CLOSING")


class AncestorCounters:
    def __init__(self):
        self.visits = self.attempts = self.normal = self.fallbacks = 0

    def summary(self):
        return dict(member_visits=self.visits, fresh_stat_attempts=self.attempts,
            ordinary_snapshot_decisions=self.normal, original_fallbacks=self.fallbacks,
            original_all_ancestors_and_file_required_check_retained=True,
            snapshot_cached_between_member_visits=False, original_reparse_or_error_fallback_retained=True,
            original_default_direct_path_mutated=False, extra_sampler_query_thread_or_process=False,
            PC_freeze_resolved=False)


def ancestor_link_free(member, counts, *, query=os.stat):
    counts.visits += 1
    counts.attempts += 1
    try:
        value = query(member, follow_symlinks=False)
    except OSError:
        counts.fallbacks += 1
        return not member.is_symlink() and not member.is_junction()
    attrs, tag, mode = (getattr(value, n, None) for n in ("st_file_attributes", "st_reparse_tag", "st_mode"))
    ordinary = (type(attrs) is int and 0 <= attrs <= 0xffffffff
        and type(tag) is int and tag == 0 and type(mode) is int and mode >= 0
        and not attrs & (snapshot.REPARSE | snapshot.DEVICE)
        and bool(attrs & snapshot.DIRECTORY) == stat.S_ISDIR(mode))
    if not ordinary:
        counts.fallbacks += 1
        return not member.is_symlink() and not member.is_junction()
    counts.normal += 1
    return True


def ancestor_projection(raw, environment, counts, *, predicate=ancestor_link_free):
    require(type(raw) is bytes and len(raw) == ORIGINAL_BUILD_PIN["bytes"]
        and hashlib.sha256(raw).hexdigest() == ORIGINAL_BUILD_PIN["sha256"], "EXACT_ORIGINAL_BUILD_BYTES")
    nodes = [n for n in ast.parse(raw.decode("utf-8")).body
        if isinstance(n, ast.FunctionDef) and n.name == "direct_path"]
    require(len(nodes) == 1, "ONE_ORIGINAL_DIRECT_PATH")
    node = copy.deepcopy(nodes[0])
    before = ast.dump(node, include_attributes=False)
    target = ast.dump(ast.parse("not member.is_symlink() and not member.is_junction()", mode="eval").body, include_attributes=False)
    changes = 0
    class Project(ast.NodeTransformer):
        def visit_BoolOp(self, value):
            nonlocal changes
            if ast.dump(value, include_attributes=False) == target:
                changes += 1
                new = ast.parse("_ancestor_link_free(member)", mode="eval").body
                new._original_pair = copy.deepcopy(value)
                return new
            return self.generic_visit(value)
    node = Project().visit(node)
    require(changes == 1, "ONE_LINK_PAIR_ONLY")
    class Undo(ast.NodeTransformer):
        def visit(self, value):
            if hasattr(value, "_original_pair"):
                return copy.deepcopy(value._original_pair)
            return super().visit(value)
    require(ast.dump(Undo().visit(copy.deepcopy(node)), include_attributes=False) == before, "ALL_ORIGINAL_DIRECT_PATH_AST")
    env = dict(environment, _ancestor_link_free=lambda member: predicate(member, counts))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), ORIGINAL_BUILD_PIN["path"], "exec"), env)
    return env["direct_path"], dict(original_direct_path_AST_restored_exactly=True,
        changed_link_predicate_pairs=1, every_ancestor_visit_and_final_file_check_retained=True,
        original_source_method_code_closure_and_pin_shape_retained=True,
        no_snapshot_cache_or_default_module_mutation=True, runtime_or_freeze_resolution_qualified=False)


def build_bytes():
    pin = ORIGINAL_BUILD_PIN
    base.stable.stable.prior.build.direct_path(c.ROOT / pin["path"], file_required=True)
    with (c.ROOT / pin["path"]).open("rb") as stream:
        raw = stream.read(pin["bytes"] + 1)
    require(len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"], "EXACT_BUILD_BOOTSTRAP_BYTES")
    return raw



def require(ok, code):
    if not ok:
        raise ValueError("SOURCE_STAT_CONNECTION_" + code)


def attempt(index):
    require(type(index) is int and 127 <= index <= 249, "INDEX")
    return 2 if index == 127 else 1


def data_path(index):
    attempt(index)
    return f"implementation/p09/evidence/p09-361-case{index}-source-stat-connection-data002.v1.json"


def validate_data(row, step):
    require(type(row) is dict and set(row) == {"schema_version", "index", "before", "run",
        "base_step_pin", "prior_chunk_data_pin", "failed_runtime_pins",
        "source_qualification_pin", "connection_qualification_pin", "connection_code_pins", "prior_source_data_pin",
        "prior_source_code_pins", "failed_preflight_pin"}, "DATA_SHAPE")
    a.fields(row, dict(schema_version="hwpx-agent.p09-flat-source-stat-connection/v2",
        index=step.index, before=step.before, run=attempt(step.index)), "DATA_CURSOR")
    a.exact(row["base_step_pin"], step.pin, "BASE_STEP")
    require(set(base.scope.pins([row["prior_chunk_data_pin"]], 1)) == {prior.data_path(step.index)}, "PRIOR_DATA_PATH")
    a.exact(row["failed_runtime_pins"], [FAILED127] if step.index == 127 else [], "REVIEWED_FAILURE_ONLY")
    for key, path in (("source_qualification_pin", QUALIFICATION_PATH),
                      ("connection_qualification_pin", CODE_QUALIFICATION_PATH)):
        require(set(base.scope.pins([row[key]], 1)) == {path}, "QUALIFICATION_PATH")
    require(set(base.scope.pins(row["connection_code_pins"], len(FILES))) == set(FILES), "ALL_FIXED_CODE")
    require(set(base.scope.pins(row["prior_source_code_pins"], len(PRIOR_SOURCE_FILES))) == set(PRIOR_SOURCE_FILES), "PRIOR_SOURCE_CODE")
    if step.index == 127:
        require(set(base.scope.pins([row["prior_source_data_pin"]], 1)) == {prior_source_data_path(127)}, "PRIOR_SOURCE_DATA_PATH")
        a.exact(row["failed_preflight_pin"], FAILED_PREFLIGHT, "PRESERVED_FAILED_PREFLIGHT")
    else:
        a.exact(row["prior_source_data_pin"], None, "NO_INVENTED_PRIOR_DATA")
        a.exact(row["failed_preflight_pin"], None, "NO_INVENTED_FAILED_PREFLIGHT")
    return row


def connection_data(q):
    require(base.CONFIG is not None, "CONFIG_REQUIRED")
    text = q.text(data_path(base.CONFIG.index))
    require(0 < len(text.encode("utf-8")) <= 16384, "BOUNDED_DATA")
    return validate_data(json.loads(text, object_pairs_hook=base.unique), base.CONFIG)


def review_failure(row):
    a.fields(row, dict(state="DEFERRED_NOT_STARTED", selected_test_index=127,
        stop_reason="STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME", worker_created=False,
        product_body_observed=False, Native_source_frame_qualified=False,
        current_generation_runtime_candidate_qualified=False, cleanup_confirmed=True,
        owned_tree_empty=True, accepted_count_delta=0, full249_current_qualified=False,
        signed16_current_qualified=False, P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN"), "PREBODY_FAILURE")
    a.exact(row["source_freeze"], [], "NO_FAILED_COMMITTED_SOURCE")
    a.exact(row["source_frame"], None, "NO_FAILED_NATIVE_FRAME")
    a.exact(row["passed_test_names"], [], "NO_PREVIOUS_PRODUCT_BODY_REPLAY")
    return True


def own_reviewed_inputs(q, run):
    row = connection_data(q)
    a.exact(run, row["run"], "EXPLICIT_REVIEWED_ATTEMPT")
    old = prior.own_reviewed_inputs(q, prior.attempt(base.CONFIG.index))
    a.exact(q.snapshots[prior.data_path(base.CONFIG.index)], row["prior_chunk_data_pin"], "PRIOR_DATA_UNCHANGED")
    qualification = a.read_exact(q, row["source_qualification_pin"])
    a.fields(qualification, dict(state="PASS_STOP127_REVIEW_AND_SOURCE_STAT10_NOT_RUNTIME127_OR_GATE",
        accepted_count_after=120, accepted_count_delta=0, next_runtime_index=127,
        P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN", full249_current_qualified=False), "SOURCE_QUAL_NOT_PRODUCT")
    small = qualification["candidate_qualification"]
    a.fields(small, dict(state="PASS_SOURCE_STAT10_AND_BOUNDED_REAL_WINDOWS_READER_NOT_RUNTIME127",
        actual127_product_executed=False, accepted_count_delta=0, cleanup_confirmed=True,
        Native_or_product_runtime_qualified=False, PC_freeze_resolved=False), "BOUNDED_CANDIDATE")
    a.fields(small["contracts"], dict(run=10, errors=0, failures=0, skips=0), "SOURCE10")
    for pin in small["code_pins"] + row["connection_code_pins"]:
        a.exact(q.pin(pin["path"]), pin, "QUALIFIED_SOURCE_BYTES")
    review_prior_source(q, row)
    a.exact(q.pin(ORIGINAL_BUILD_PIN["path"]), ORIGINAL_BUILD_PIN, "EXACT_ORIGINAL_BUILD_SOURCE")
    connected = a.read_exact(q, row["connection_qualification_pin"])
    a.fields(connected, dict(state="PASS_SOURCE_STAT_ANCESTOR_CONNECTION22_AND_SOURCE10_NOT_FULL_PREFLIGHT_OR_RUNTIME",
        actual127_product_executed=False, accepted_count_after=120, accepted_count_delta=0,
        cleanup_confirmed=True, Native_or_product_runtime_qualified=False), "CONNECTION_QUAL_NOT_PRODUCT")
    a.fields(connected["contracts"], dict(run=32, errors=0, failures=0, skips=0), "CONNECTION32")
    a.exact(connected["new_code_pins"], row["connection_code_pins"], "EXACT_TESTED_CONNECTION_CODE")
    a.exact(q.pin(snapshot.ORIGINAL_PIN["path"]), snapshot.ORIGINAL_PIN, "EXACT_ORIGINAL_LEAF")
    for pin in row["failed_runtime_pins"]:
        review_failure(a.read_exact(q, pin))
    return row, old


def reviewed_inputs(q, run):
    row, old = own_reviewed_inputs(q, run)
    prior.prior.reviewed_inputs(q, prior.prior.attempt(base.CONFIG.index))
    a.exact(q.snapshots[prior.prior.data_path(base.CONFIG.index)], old["prior_terminal_data_pin"], "PRIOR_TERMINAL_DATA")
    return row


def binding_attempt(q, run):
    reviewed_inputs(q, run)
    required, rust = base.binding(q)
    return base.scope.extend(required, q.snapshots), rust


def context(step):
    return NS(**{**vars(prior.context(step)), "SELF": SELF, "TEST": TEST})


def connect_engine(engine, raw):
    old = FunctionType(prior.connect_engine.__code__, dict(vars(prior), SELF=SELF, TEST=TEST),
        argdefs=prior.connect_engine.__defaults__)(engine, raw)
    environment = engine.run_owned.__globals__
    build = environment["build"]
    # BuildReader._source also validates pin shape and every ancestor via
    # direct_path. Insert the optimized Audit leaf below those wrappers instead
    # of overriding the top-level method and accidentally bypassing them.
    SourceLeaf, proof = snapshot.reader_type(snapshot.original.AuditEvidenceReader, raw)

    original_source = build.BuildReader._source
    original_direct = original_source.__globals__["direct_path"]
    require(original_direct is base.stable.stable.prior.build.direct_path, "EXACT_ORIGINAL_DIRECT_PATH")
    build_raw = build_bytes()

    class BuildReader(build.BuildReader, SourceLeaf):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            self._ancestor_counters = AncestorCounters()
            direct, direct_proof = ancestor_projection(build_raw, original_direct.__globals__, self._ancestor_counters)
            env = dict(original_source.__globals__, direct_path=direct)
            self._original_source_with_ancestor = FunctionType(original_source.__code__, env,
                argdefs=original_source.__defaults__, closure=original_source.__closure__).__get__(self, type(self))
            self._ancestor_projection_proof = direct_proof

        def _source(self, name):
            # Identical original source-method code, including its __class__
            # closure/super, pin-shape checks and ancestor/output predicates.
            return self._original_source_with_ancestor(name)

        def ancestor_snapshot_diagnostics(self):
            return self._ancestor_counters.summary()

    require(tuple(x for x in BuildReader.__mro__[1:] if x is not SourceLeaf) == build.BuildReader.__mro__, "EXACT_ORIGINAL_BUILD_MRO")
    proof = dict(proof, original_build_source_pin_shape_and_ancestor_wrappers_retained=True,
        optimized_source_leaf_inserted_below_original_wrappers=True)
    original_summary = build.pressure_summary

    def pressure_summary(guard):
        return dict(original_summary(guard), single_snapshot_metadata_source=guard.reader.source_snapshot_diagnostics(),
            single_snapshot_ancestor_source=guard.reader.ancestor_snapshot_diagnostics())

    environment["build"] = NS(**{**vars(build), "BuildReader": BuildReader, "pressure_summary": pressure_summary})
    return dict(original_chunk_connection=old, source_stat_factory=proof,
        metadata_reader_only=True, held_Native_boundary_source_adapter_changed=False,
        original_engine_bytecode_unchanged=True, original_build_default_reader_mutated=False,
        extra_sampler_query_thread_or_process=False, runtime_product_connection_qualified=False)


def template():
    return FunctionType(prior.template.__code__, dict(vars(prior), SELF=SELF, TEST=TEST,
        connect_engine=connect_engine), argdefs=prior.template.__defaults__)()


def worker(task):
    a.exact(base.run_for(task), attempt(base.CONFIG.index), "EXACT_WORKER_ATTEMPT")
    engine, _ = template()
    return engine.worker(task)


def run_owned(run):
    a.exact(run, attempt(base.CONFIG.index), "EXPLICIT_REVIEWED_RUN")
    environment = dict(prior.run_owned.__globals__, attempt=attempt, template=template, binding_attempt=binding_attempt)
    return FunctionType(prior.run_owned.__code__, environment, argdefs=prior.run_owned.__defaults__)(run)


def preflight_projection(raw, leaf):
    unchanged = prior.preflight_projection(raw, leaf)
    old = unchanged.__code__
    constants = tuple("-source-stat-ancestor-preflight001.v1.json" if x == "-chunk-preflight001.v1.json" else x for x in old.co_consts)
    require(sum(type(x) is str and x == "-chunk-preflight001.v1.json" for x in old.co_consts) == 1, "ONE_FRESH_PREFLIGHT_DESTINATION")
    projected = old.replace(co_consts=constants)
    require(projected.replace(co_consts=old.co_consts) == old, "ALL_ORIGINAL_PREFLIGHT_BYTECODE")
    Reader, proof = snapshot.reader_type(unchanged.__globals__["a"].AcceptanceReader, leaf)
    instances = []

    class PreflightReader(Reader):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            require(not instances, "ONE_PREFLIGHT_READER")
            instances.append(self)

    old_dump = unchanged.__globals__["json"].dump

    def dump(row, stream, **kw):
        diagnostics = instances[0].source_snapshot_diagnostics() if instances else dict(source_requests=0)
        return old_dump(dict(row, single_snapshot_preflight_source=diagnostics, single_snapshot_projection_proof=proof), stream, **kw)

    environment = dict(unchanged.__globals__, SELF=SELF, TEST=TEST, template=template,
        connection_data=connection_data, binding_attempt=binding_attempt, data_path=data_path,
        a=NS(**{**vars(a), "AcceptanceReader": PreflightReader}), json=NS(**{**vars(json), "dump": dump}))
    return FunctionType(projected, environment, argdefs=unchanged.__defaults__)


def preflight():
    pin = prior.prior.prior.METADATA_PIN
    base.stable.stable.prior.build.direct_path(c.ROOT / pin["path"], file_required=True)
    with (c.ROOT / pin["path"]).open("rb") as stream:
        raw = stream.read(pin["bytes"] + 1)
    return preflight_projection(raw, prior.leaf_bytes())()


def actual_source_binding(row):
    metadata = row["bootstrap_metadata"]
    diag = metadata["early_pressure"]["single_snapshot_metadata_source"]
    a.fields(diag, dict(original_logical_source_predicates_retained=True,
        stat_result_cached_or_reused_between_source_requests=False, original_default_reader_mutated=False,
        held_Native_path_guard_replaced=False, extra_sampler_query_thread_or_process=False,
        complete_source_reads_rates_or_deadlines_reduced=False, PC_freeze_resolved=False), "ACTUAL_SOURCE_GUARDS")
    for name in ("source_requests", "fresh_no_follow_stat_attempts", "ordinary_windows_snapshot_decisions",
                 "exact_original_fallback_requests", "ordinary_nonfile_rejections"):
        require(type(diag.get(name)) is int and diag[name] >= 0, "REAL_INTEGER_SOURCE_COUNTS")
    a.exact(diag["source_requests"], metadata["read_passes"], "EVERY_ACTUAL_SOURCE_REQUEST")
    a.exact(diag["fresh_no_follow_stat_attempts"], diag["source_requests"], "EVERY_FRESH_STAT_ATTEMPT")
    a.exact(diag["ordinary_windows_snapshot_decisions"] + diag["exact_original_fallback_requests"], diag["source_requests"], "ALL_DECISIONS_ACCOUNTED")
    require(diag["ordinary_windows_snapshot_decisions"] > 0, "ACTUAL_OPTIMIZATION_NOT_IMPORT_ONLY")
    a.exact(diag["ordinary_nonfile_rejections"], 0, "NO_ACCEPTED_NONFILE_REJECTION")
    ancestor = metadata["early_pressure"]["single_snapshot_ancestor_source"]
    a.fields(ancestor, dict(original_all_ancestors_and_file_required_check_retained=True,
        snapshot_cached_between_member_visits=False, original_reparse_or_error_fallback_retained=True,
        original_default_direct_path_mutated=False, extra_sampler_query_thread_or_process=False,
        PC_freeze_resolved=False), "ANCESTOR_GUARDS")
    for name in ("member_visits", "fresh_stat_attempts", "ordinary_snapshot_decisions", "original_fallbacks"):
        require(type(ancestor.get(name)) is int and ancestor[name] >= 0, "ANCESTOR_INTEGER_COUNTS")
    require(ancestor["member_visits"] >= metadata["read_passes"] and ancestor["ordinary_snapshot_decisions"] > 0, "ACTUAL_ANCESTOR_USAGE")
    a.exact(ancestor["fresh_stat_attempts"], ancestor["member_visits"], "FRESH_EVERY_ANCESTOR")
    a.exact(ancestor["ordinary_snapshot_decisions"] + ancestor["original_fallbacks"], ancestor["member_visits"], "ALL_ANCESTORS_ACCOUNTED")
    return True


def validator(raw, ctx, flat=True):
    project, proof = prior.validator(raw, ctx, flat)
    project.__globals__["CONTROLLERS"] = tuple(dict.fromkeys(project.__globals__["CONTROLLERS"] + FILES))
    return project, dict(proof, source_stat_controller_pins_added=True)


def validate_candidate(q, row, listing, oldbody, fresh, ctx, flat=True):
    environment = dict(prior.validate_candidate.__globals__, validator=validator)
    evidence, proof = FunctionType(prior.validate_candidate.__code__, environment,
        argdefs=prior.validate_candidate.__defaults__)(q, row, listing, oldbody, fresh, ctx, flat)
    actual_source_binding(row)
    proof["actual_metadata_source_snapshot_usage_checked"] = True
    return evidence, proof


def root_path(step):
    return f"implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run{attempt(step.index):03}.v1.json"


def prepare_projection(raw):
    environment = dict(prior.accepted.prior.metadata.prepare_projection.__globals__,
        root_path=root_path, validate_candidate=validate_candidate, runtime=NS(context=context))
    return FunctionType(prior.accepted.prior.metadata.prepare_projection.__code__, environment,
        argdefs=prior.accepted.prior.metadata.prepare_projection.__defaults__)(raw)


def prepare(q, root_pin):
    data, old = own_reviewed_inputs(q, attempt(base.CONFIG.index))
    environment = dict(prior.accepted.prepare.__globals__, prepare_projection=prepare_projection)
    row, listing, evidence, proof = FunctionType(prior.accepted.prepare.__code__, environment,
        argdefs=prior.accepted.prepare.__defaults__)(q, root_pin)
    a.exact(q.snapshots[prior.prior.data_path(base.CONFIG.index)], old["prior_terminal_data_pin"], "ACCEPT_TERMINAL_DATA")
    expected = base.scope.pins(row["source_freeze"])
    pins = data["connection_code_pins"] + data["prior_source_code_pins"] + old["connection_code_pins"] + [
        ORIGINAL_BUILD_PIN, PRIOR_CONNECTION_QUAL,
        data["source_qualification_pin"], data["connection_qualification_pin"], prior.QUALIFICATION,
        old["connection_qualification_pin"], snapshot.ORIGINAL_PIN] + data["failed_runtime_pins"]
    if data["failed_preflight_pin"] is not None:
        pins += [data["failed_preflight_pin"], data["prior_source_data_pin"]]
    if old["failed_preflight_pin"] is not None:
        pins.append(old["failed_preflight_pin"])
    for pin in pins:
        a.exact(expected[pin["path"]], pin, "ALL_SOURCE_CHUNK_CODE_QUAL_AND_FAILURE_IN_NATIVE_FRAME")
    for name in (data_path(base.CONFIG.index), prior.data_path(base.CONFIG.index), prior.prior.data_path(base.CONFIG.index)):
        a.exact(expected[name], q.snapshots[name], "ALL_DATA_INSIDE_FRAME")
    return row, listing, evidence, proof


def accept(root_pin):
    require(type(root_pin) is dict and root_pin.get("path") == root_path(base.CONFIG), "EXACT_CANONICAL_ROOT")
    pin = prior.accepted.original.candidate.ACCEPTOR_PIN
    with (c.ROOT / pin["path"]).open("rb") as stream:
        raw = stream.read(pin["bytes"] + 1)
    execute, _ = prior.accepted.original.run_projection(raw, root_pin)
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
        code = str(exc) if isinstance(exc, ValueError) else "REDACTED_SOURCE_STAT_CONNECTION_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED", error_code=code
            if re.fullmatch("[A-Z0-9_]{1,256}", code) else "REDACTED_SOURCE_STAT_CONNECTION_FAILURE")))
        raise SystemExit(2) from None

