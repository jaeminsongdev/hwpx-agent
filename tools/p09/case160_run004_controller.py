"""One explicit run004 controller; preserved run003 is never overwritten.

새 controller 안에서 준비·graph·worker·독립 결과검사를 연결한다.
완료된 run003 준비는 선행 입력 증거일 뿐 새 preflight나 GO가 아니다.
새 helper는 pinned private namespace로 읽으며 sys.modules를 숨기지 않는다.
"""
import argparse
import json
import re
import sys
from types import CodeType, FunctionType, SimpleNamespace as NS
import flat_current_queue_envelope_runtime_v25 as old

SELF = "tools/p09/case160_run004_controller.py"
TEST = "tools/p09/tests/test_case160_run004_controller.py"
DATA = "implementation/p09/evidence/p09-361-case160-envelope-controller-data040.v1.json"
QUAL = "implementation/p09/evidence/p09-361-case160-run004-controller-r373.v1.json"
PREFLIGHT = "implementation/p09/evidence/p09-361-case160-envelope-controller-preflight040.v1.json"
QUAL_STATE = "PASS_RUN004_CONTROLLER_CONNECTION_NOT_WHOLE_PREFLIGHT_NATIVE_OR_GO"
SCHEMA = "hwpx-agent.p09-case160-run004-controller/v1"
BINDING_CODE = "implementation/p09/evidence/p09-361-run004-parent34-binding-code5-r858.v1.json"
PREDECESSOR_PIN = dict(path="tools/p09/flat_current_queue_envelope_runtime_v31.py", bytes=14869,
    sha256="d6315996ac1cc8e343d9049eda2a46db9dd0cf7c1561f8f99664bc285913eec1")
NEW_PINS = [
    dict(path="tools/p09/prepared_input_checkpoint_v1.py",bytes=3715,sha256="0e9189b0cdb51588520cb14e15a1f30440e9b8eecdc08111afaa6ab2d9147143"),
    dict(path="tools/p09/preparation_terminal_progress_v1.py",bytes=1473,sha256="4ee6983d3e2488f432f3975c7d8b5901edd379e95c79927630028bf2c3e04b5f"),
    dict(path="tools/p09/terminal_metadata_pressure_v1.py",bytes=2956,sha256="7b5bb9b890cde566f566857c06f010736519ac6e2551480dcf92bdab6dfdd9dd"),
    dict(path="tools/p09/distinct_final_sample_guard_v1.py",bytes=1683,sha256="8c590aa82c2677d391d6d5781b356641f77c7cdc6e55370ca251d6a809ad67c3"),
    dict(path="tools/p09/prepared_scope_handoff_v1.py",bytes=6933,sha256="4f744b4abb762a1209265d94874263f71375dc1bb40e70fe008c1afc503a78c7"),
    dict(path="tools/p09/prepared_checkpoint_transport_v1.py",bytes=3402,sha256="8d997545ee54a1efe992170864cf3b3c0e06fd14e29ed0cb810861ed1ae5b89d"),
    dict(path="tools/p09/compact_worker_capsule_wire_v1.py",bytes=5168,sha256="2649fcca9479ae889b71b548e7a079357121b5df0a127c7cd85d66671cd9e7bd"),
    dict(path="tools/p09/review_failed_run003_v1.py",bytes=3077,sha256="bda5288b72fac5eb4fd2cdf99e3e593acadbc86338cb610356a2b07dbaf3777e"),
    dict(path="tools/p09/runtime_failed160_extras_v1.py",bytes=6557,sha256="9a1f773aac6683705fa1cfae7a10f9d0c9eba02db2822bca0ef9578afa0005a3"),
    dict(path="tools/p09/runtime_successor_manifest_v7.py",bytes=4019,sha256="00a8f0a41c8bff7f79a9eff95aa198404d750204552d0e442264adb1066cde66"),
    dict(path="tools/p09/runtime_successor_manifest_v8.py",bytes=3781,sha256="603440b4f38c30c83cde6f94306916bfccd6859c1db05fb7d7a7423fa3103b08"),
    dict(path="tools/p09/successor_runtime_graph_v6.py",bytes=1580,sha256="9699aaf4fb458c5a5744a132f0bc7fd1f1b37359ac35a376ae27e6b5402d33a1"),
    dict(path="tools/p09/successor_runtime_graph_v7.py",bytes=1778,sha256="ea7baf94fff33a1cf0db1f5a0396c16e9345b99f69f9bac7653cda48966050a7"),
    dict(path="tools/p09/successor_bounded_graph_bootstrap_v6.py",bytes=5230,sha256="024f19bb79d26c970d4fb4a94df360b3e22df4f7beea8e6b7c60ac65996c7343"),
    dict(path="tools/p09/successor_bounded_graph_bootstrap_v7.py",bytes=3368,sha256="8bcd60517a440c9faaa3489ee56420c225013a134c2771117dac232ddc05ce81"),
    dict(path="tools/p09/successor_current_binding_v6.py",bytes=3845,sha256="5257006d22114fa90c415c3c1a66fa6249191730ee17bf09891625a5df5ef024"),
    dict(path="tools/p09/successor_current_binding_v7.py",bytes=3031,sha256="5a0d0f4424335b4fdc5ff596a180e27770252c216116375af70bc08db3ca6550"),
    dict(path="tools/p09/reviewed_case160_attempt_v3.py",bytes=2483,sha256="6de4709a941e9e359dd7e7ceb3b50159f87510573dda3a75f0906c11ff62d279"),
]
PREVIOUS, previous_proof = old.namespace_bundle.load(old.c.ROOT, [PREDECESSOR_PIN],
    {"flat_current_queue_envelope_runtime_v25": old})
predecessor = PREVIOUS.flat_current_queue_envelope_runtime_v31
a = old.a

# Explicit known source graphs only; no recursive sys.modules harvesting.
reuse = dict(vars(old._namespaces))
reuse["flat_current_queue_envelope_runtime_v25"] = old
cursor = predecessor
while hasattr(cursor, "PRIOR160"):
    reuse.update(vars(cursor.NEXT))
    cursor = cursor.PRIOR160
reuse.update(vars(cursor.NEXT))
reuse.update(vars(cursor.PRIOR159.SOURCE_NAMESPACES))
FIRST, first_proof = old.namespace_bundle.load(old.c.ROOT, NEW_PINS[:9], reuse)
reuse.update(vars(FIRST))
NEXT, next_proof = old.namespace_bundle.load(old.c.ROOT, NEW_PINS[9:], reuse)
SOURCE_PROOFS = predecessor.SOURCE_PROOFS + previous_proof + first_proof + next_proof
RAW_PINS = predecessor.RAW_PINS + [PREDECESSOR_PIN] + NEW_PINS
bootstrap = NEXT.successor_bounded_graph_bootstrap_v7
binding_module = NEXT.successor_current_binding_v7
attempt = NEXT.reviewed_case160_attempt_v3
MANIFEST = bootstrap.MANIFEST
CAPSULE = bootstrap.CAPSULE
DISTINCT_TEMPLATE, RETRY, ATTEMPT_PROOF = attempt.connect_template(old.prior)
prior = NS(**{**vars(old.prior), "template": DISTINCT_TEMPLATE})


def clone_family(family, replacements):
    env = dict(family)
    for name, fn in family.items():
        if type(fn) is FunctionType and fn.__globals__ is family:
            copy = FunctionType(fn.__code__, env, argdefs=fn.__defaults__, closure=fn.__closure__)
            copy.__kwdefaults__ = fn.__kwdefaults__
            env[name] = copy
    env.update(replacements)
    return env


_env = clone_family(predecessor._env, dict(SELF=SELF, TEST=TEST, DATA=DATA, QUAL=QUAL,
    QUAL_STATE=QUAL_STATE, SCHEMA=SCHEMA, PREFLIGHT=PREFLIGHT, BINDING_CODE=BINDING_CODE,
    bootstrap=bootstrap, CAPSULE=CAPSULE, MANIFEST=MANIFEST, RETRY=RETRY, prior=prior,
    _graph=None, _checkpoint=None, _execution_requested=False, PARENT_STATES=[]))

# Only worker task metadata changes; preserve the entire existing function body.
worker_fn = _env["worker"]
worker_code = worker_fn.__code__
old_task = "case160-current-r003-tests"
a.require(sum(type(x) is str and x == old_task for x in worker_code.co_consts) == 1, "ONE_RUN004_WORKER_TASK")
worker_changed = worker_code.replace(co_consts=tuple(attempt.TASK if type(x) is str and x == old_task else x
    for x in worker_code.co_consts))
a.require(worker_changed.replace(co_consts=worker_code.co_consts) == worker_code, "ENTIRE_RUN004_WORKER_BODY_INVERSE")
worker_projected = FunctionType(worker_changed, _env, argdefs=worker_fn.__defaults__, closure=worker_fn.__closure__)
worker_projected.__kwdefaults__ = worker_fn.__kwdefaults__
_env["worker"] = worker_projected


def validate_data(row):
    _env["only160"]()
    a.require(type(row) is dict and set(row) == {
        "schema_version", "index", "before", "run", "physical_product_run", "base_step_pin",
        "authority_pin", "prior_runtime_pin", "manifest_pin", "capsule_pin", "qualification_pin",
        "controller_code_pins", "binding_code_pin"}, "CLOSED_RUN004_DATA")
    successor = predecessor._env["current_binding"].successor
    a.fields(row, dict(schema_version=SCHEMA, index=160, before=153, run=1, physical_product_run=4,
        base_step_pin=old.base.CONFIG.pin, authority_pin=successor.AUTHORITY, prior_runtime_pin=successor.ROOT,
        manifest_pin=MANIFEST, capsule_pin=CAPSULE), "EXACT_RUN004_DATA_AND_UNCHANGED_AUTHORITY")
    a.exact(set(old.base.scope.pins(row["controller_code_pins"], 2)), {SELF, TEST}, "EXACT_RUN004_CODE_PAIR")
    a.exact(row["qualification_pin"]["path"], QUAL, "EXACT_RUN004_QUALIFICATION")
    a.exact(row["binding_code_pin"]["path"], BINDING_CODE, "EXACT_CURRENT34_BINDING")
    old.base.scope.pins([row["qualification_pin"], row["binding_code_pin"]], 2)
    return row


def own_inputs(q):
    _env["_checkpoint"] = q.checkpoint
    row = validate_data(q.json(DATA))
    code = a.read_exact(q, row["qualification_pin"])
    a.fields(code, dict(state=QUAL_STATE, cleanup_confirmed=True, product_or_Native_executed=False,
        GO_authorized=False, queue_acceptance_called=False), "EXACT_RUN004_CODE_NOT_PRODUCT")
    a.exact(code["contracts"], dict(run=20, errors=0, failures=0, skipped=0), "ALL_CONTROLLER_TESTS")
    a.exact(code["new_code_pins"], row["controller_code_pins"], "QUALIFIED_CURRENT_CONTROLLER_BYTES")
    for pin in code["source_pins"] + row["controller_code_pins"] + RAW_PINS + [predecessor.RAW_TEST_PIN]:
        a.exact(q.pin(pin["path"]), pin, "ALL_REAL_RUN004_SOURCES")
    bound = a.read_exact(q, row["binding_code_pin"])
    a.fields(bound, dict(state="PASS_RUN004_FULL_PARENT34_BINDING_CODE5_SAME_BOUNDED_GRAPH_NOT_CONTROLLER_OR_GO",
        source_pairs=34, rust_source_count=787, original600_cost_accepted=True, cleanup_confirmed=True,
        Native_or_product_executed=False, GO_authorized=False), "EXACT_PARENT34_NOT_RUNTIME_PERMISSION")
    a.require(bound["fresh_inputs"] == bound["final_fresh_hashes"] > 0, "ALL_PARENT34_FINAL_HASHES")
    for pin in bound["source_pins"]:
        a.exact(q.pin(pin["path"]), pin, "CURRENT_PARENT34_SOURCES")
    # Preserve the whole qualified predecessor admission and its exact reviews.
    predecessor.owned(q)
    attempt.reviewed_failure(q, a)
    a.exact(q.pin(MANIFEST["path"]), MANIFEST, "ACTUAL_RUN004_MANIFEST")
    a.exact(q.pin(CAPSULE["path"]), CAPSULE, "ACTUAL_RUN004_CAPSULE")
    return row


owned, ADMISSION_COUNTS = old.admission_once.connect(own_inputs)


def binding(q):
    owned(q)
    # The explicit old controller supplies only the provenance context of r834;
    # new DATA/PREFLIGHT are separately required and may never be labeled r834.
    complete, rust, graph, live, proof = binding_module.bind(q, predecessor)
    binding_module.same_graph(a, live, graph.binding)
    _env["_graph"] = graph
    _env["_checkpoint"] = q.checkpoint
    if _env["_execution_requested"]:
        checked = q.json(PREFLIGHT)
        a.fields(checked, dict(state="PASS_REVIEWED_METADATA_CONNECTION_PREFLIGHT_NOT_NATIVE_OR_PRODUCT_OR_ACCEPTANCE",
            index=160, product_worker_or_Native_frame_executed=False, cleanup_confirmed=True,
            runtime_connection_qualified=False, accepted_count_delta=0), "NEW_RUN004_WHOLE_PREFLIGHT_REQUIRED")
        a.exact(checked["connection_data_pin"], q.snapshots[DATA], "NEW_RUN004_DATA_NOT_PREDECESSOR_DATA")
        a.require(checked["fresh_inputs"] == checked["final_fresh_hashes"] > 0, "ALL_NEW_PREFLIGHT_FINAL_HASHES")
        a.require(checked.get("synthetic_fixture_only_not_evidence", False) is False, "NO_SYNTHETIC_PREFLIGHT")
        a.resource_history(checked["resource_samples"])
    return old.base.scope.extend(complete, q.snapshots), rust


_env.update(own_inputs=owned, validate_data=validate_data, binding=binding)
# Retain the entire existing preflight body, changing only its destination.
fn = _env["preflight_projection"]
before = "-envelope-controller-preflight039.v1.json"
after = "-envelope-controller-preflight040.v1.json"
a.require(sum(type(x) is str and x == before for x in fn.__code__.co_consts) == 1, "ONE_RUN004_PREFLIGHT_DESTINATION")
changed = fn.__code__.replace(co_consts=tuple(after if type(x) is str and x == before else x for x in fn.__code__.co_consts))
a.require(changed.replace(co_consts=fn.__code__.co_consts) == fn.__code__, "ENTIRE_RUN004_PREFLIGHT_CODE_INVERSE")
projected = FunctionType(changed, _env, argdefs=fn.__defaults__, closure=fn.__closure__)
projected.__kwdefaults__ = fn.__kwdefaults__
_env["preflight_projection"] = projected

source_projection = prior.LINK.clone(prior.CURRENT_SOURCE.prepare_projection,
    root_path=RETRY.root_path, validate_candidate=_env["validate_candidate"], runtime=NS(context=_env["context"]))
source = NS(**{**vars(prior.CURRENT_SOURCE), "prepare_projection":source_projection,
    "validate_candidate":_env["validate_candidate"]})
_env["CURRENT_SOURCE"] = source
_api_env = clone_family(predecessor._api_env, dict(SELF=SELF, TEST=TEST, FILES=(SELF, TEST), QUAL_PATH=QUAL,
    source=source, own_inputs=owned, validator=_env["validator"], context=_env["context"],
    template=_env["template"], binding=binding, binding_attempt=_env["binding_attempt"]))
API = NS(**_api_env)
_env["API"] = API
M = NS(**_env)


def prepare_candidate(q, root_pin):
    """Read-only independent current160 oracle; never writes official counts."""
    M.only160()
    a.exact(root_pin["path"], RETRY.root_path(old.base.CONFIG), "EXACT_RUN004_INDEPENDENT_ROOT")
    complete, _ = binding(q)
    graph = _env["graph_value"]()
    inherited = API.inherited_for_step(q, old.base.CONFIG)
    # Independent declarations come from the exact predecessor and fresh parent
    # admission, never from the current candidate's observed source_freeze.
    inherited = old.base.scope.extend(inherited, complete)
    frozen = predecessor._api_env["source"].prior.accepted.original
    raw = q.text(frozen.SELF).encode("utf-8")

    def projector(generator, *args, **kwargs):
        factory = lambda raw, ctx, flat=True: (generator, {})
        scoped, _ = API.previous.scoped_validator(factory, inherited)(None, None)
        return graph.full_oracle.projector(scoped, *args, **kwargs)

    oracle = NS(**{**vars(graph.full_oracle), "projector":projector})
    private_graph = NS(**{**vars(graph), "full_oracle":oracle})
    validator = prior.LINK.clone(_env["validator"], graph_value=lambda:private_graph)
    full = prior.LINK.clone(_env["validate_candidate"], validator=validator)
    unchanged = source.prepare_projection(raw)
    unchanged.__globals__.update(validate_candidate=full,
        r=NS(**{**vars(unchanged.__globals__["r"]), "context":_env["context"]}))
    row, listing, evidence, proof = unchanged(q, root_pin)
    expected = old.base.scope.pins(row["source_freeze"])
    for pin in RAW_PINS + row_code_pins(q) + [MANIFEST, CAPSULE, q.snapshots[DATA], q.snapshots[QUAL]]:
        a.exact(expected.get(pin["path"]), pin, "ALL_CURRENT_RUN004_SOURCES_INSIDE_REAL_NATIVE_FRAME")
    RETRY.validate_actual(row, old.base.CONFIG, root_pin)
    return row, listing, evidence, dict(proof, independent_declared_scope_not_current_observations=True,
        original_frozen_prepare_and_whole_oracle_retained=True, product_or_Native_reexecuted=False,
        queue_acceptance_called=False)


def row_code_pins(q):
    return [q.snapshots[SELF], q.snapshots[TEST]]


def accept_not_qualified(*args, **kwargs):
    a.require(False, "RUN004_READ_ONLY_ORACLE_QUALIFICATION_REQUIRED_BEFORE_QUEUE_WRITE")


API.prepare = prepare_candidate
API.accept = accept_not_qualified


def run_owned(public_run):
    M.only160()
    a.require(type(public_run) is int and public_run == 4, "EXACT_PHYSICAL_RUN004_ONLY")
    a.require(not (old.c.ROOT/RETRY.root_path(old.base.CONFIG)).exists(), "NO_RUN004_RECEIPT_OVERWRITE")
    a.require((old.c.ROOT/PREFLIGHT).is_file(), "NEW_RUN004_PREFLIGHT_MISSING")
    a.require(not _env["_execution_requested"], "NO_AUTOMATIC_RUN004_RETRY")
    _env["_execution_requested"] = True
    execute, state = prior.CONNECTION.connect_run(API.run_owned, prior.BACKEND)
    before = len(prior.ATTEMPT_STATES)
    result = execute(RETRY.public_run(160, public_run))
    observed = prior.ATTEMPT_STATES[before:]
    a.require(len(observed) == 1 and observed[0].physical_product_run == 4
        and observed[0].actual_engine_calls == 1, "ONE_ORIGINAL_RUN004_ENGINE_CALL")
    a.require(state["actual_local_bindings"] == 1, "ONE_NATIVE_DIAGNOSTIC_BINDING")
    return result


def qualify():
    """One bounded source/connection qualification, no runtime dispatch."""
    import hashlib
    import io
    import os
    import time
    import unittest
    guard_type = FIRST.terminal_metadata_pressure_v1.guard_type(
        FIRST.distinct_final_sample_guard_v1.guard_type(a.Guard))
    guard = guard_type()
    started = time.monotonic()
    qualification_path = old.c.ROOT/QUAL
    data_path = old.c.ROOT/DATA
    a.require(not qualification_path.exists() and not data_path.exists(), "EXCLUSIVE_RUN004_CODE_AND_DATA")
    out = dict(state="FAILED_RUN004_CONTROLLER_NOT_ACCEPTED", accepted_count_delta=0,
        product_or_Native_executed=False, GO_authorized=False, queue_acceptance_called=False,
        whole_current_preflight_qualified=False, independent_current160_oracle_qualified=False,
        P09_gate="OPEN", PC_freeze_resolved=False)
    try:
        guard.acquire()
        old.base.configure(160)
        q = a.AcceptanceReader(old.c.ROOT, guard.check)
        code_pins = [q.pin(SELF), q.pin(TEST)]
        for p in RAW_PINS + [predecessor.RAW_TEST_PIN]:
            a.exact(q.pin(p["path"]), p, "ALL_EXACT_RUN004_SOURCE_BYTES")
        suite = unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests.test_case160_run004_controller")
        tested = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        a.require(tested.wasSuccessful() and tested.testsRun == 20 and not tested.skipped, "RUN004_CODE20")
        graph, graph_proof = bootstrap.load(old, q.checkpoint)
        for p in graph_proof["reader_source_pins"]:
            a.exact(q.pin(p["path"]), p, "EXACT_REAL_BOUNDED34_SOURCE")
        _env["_graph"] = graph
        _env["_checkpoint"] = q.checkpoint
        engine, template_proof = M.template()
        a.exact(RETRY.task(160), attempt.TASK, "ONLY_EXACT_RUN004_TASK")
        a.require(callable(engine.run_owned) and callable(engine.worker), "WHOLE_CONNECTED_ENGINE_AND_WORKER")
        a.require(all(not p["actual_module_imported_or_sys_modules_hidden"] for p in SOURCE_PROOFS), "NO_HELPER_IMPORT_HIDING")
        helper_count = sum(1 for module in sys.modules.values()
            if str(getattr(module, "__file__", "")).replace("\\", "/").find("/tools/p09/") >= 0)
        a.require(helper_count <= 64, "ORIGINAL_HELPER64_LIMIT")
        q.finish()
        guard.check(force=True)
        out.update(state=QUAL_STATE, contracts=dict(run=20, errors=0, failures=0, skipped=0),
            new_code_pins=code_pins, source_pins=[p for n,p in q.snapshots.items() if n not in (SELF, TEST)],
            source_pairs=34, bounded_graph_proof=graph_proof, template_proof=template_proof,
            actual_project_helper_count=helper_count, original_helper64_limit_preserved=True,
            whole_original_engine_worker_connected_not_executed=True,
            fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        out["error_type"] = type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}", error.args[0]):
            out["error_code"] = error.args[0]
    finally:
        guard.close()
        _env["_graph"] = None
        _env["_checkpoint"] = None
        out.update(cleanup_confirmed=guard.cleanup, elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples), default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples), default=None))
    a.require(guard.cleanup, "RUN004_QUALIFICATION_CLEANUP")

    def publish(path, row):
        raw = (json.dumps(row, ensure_ascii=True, indent=2, allow_nan=False)+"\n").encode("utf-8")
        a.require(0 < len(raw) <= 262144, "BOUNDED_RUN004_METADATA")
        for parent in (path.parent, *path.parent.parents):
            a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(), "DIRECT_METADATA_ANCESTORS")
            if parent == old.c.ROOT: break
        pacer = old._namespaces.runtime_envelope_physical_io_v1.bytes_policy.OwnedPacer()
        pacer.select(path.relative_to(old.c.ROOT).as_posix())
        with path.open("xb") as stream:
            for offset in range(0, len(raw), 65536):
                block = raw[offset:offset+65536]
                pacer.reserve(lambda:None)
                size = stream.write(block)
                a.exact(size, len(block), "ALL_METADATA_BYTES_WRITTEN")
                pacer.refund(size)
            stream.flush(); os.fsync(stream.fileno())
        return dict(path=path.relative_to(old.c.ROOT).as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    receipt = publish(qualification_path, out)
    if out["state"] == QUAL_STATE:
        successor = predecessor._env["current_binding"].successor
        binding_pin = dict(path=BINDING_CODE, bytes=48636,
            sha256="d45a04ea6aa754f3194fe8cbc8b165a6e7dc532a35a9cbdb237a43c7e6ef5f4a")
        row = dict(schema_version=SCHEMA, index=160, before=153, run=1, physical_product_run=4,
            base_step_pin=old.base.CONFIG.pin, authority_pin=successor.AUTHORITY, prior_runtime_pin=successor.ROOT,
            manifest_pin=MANIFEST, capsule_pin=CAPSULE, qualification_pin=receipt,
            controller_code_pins=out["new_code_pins"], binding_code_pin=binding_pin)
        validate_data(row)
        publish(data_path, row)
    print(json.dumps({k:out.get(k) for k in ("state", "source_pairs", "actual_project_helper_count",
        "fresh_inputs", "final_fresh_hashes", "CPU_max", "RAM_min", "cleanup_confirmed", "error_code")}))
    return 0 if out["state"] == QUAL_STATE else 1


if __name__ == "__main__":
    try:
        if len(sys.argv) == 4 and sys.argv[1:3] == ["--owned-worker", "--task"]:
            M.base.configure(M.base.task_index(sys.argv[3]))
            raise SystemExit(M.worker(sys.argv[3]))
        parser = argparse.ArgumentParser()
        parser.add_argument("--case", type=int, required=True)
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument("--run", type=int)
        mode.add_argument("--preflight", action="store_true")
        args = parser.parse_args()
        M.base.configure(args.case)
        M.only160()
        raise SystemExit(M.preflight() if args.preflight else run_owned(args.run))
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        label = str(error) if isinstance(error, ValueError) and re.fullmatch("[A-Za-z0-9_]{1,256}", str(error)) else "REDACTED_RUN004_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED", error_code=label)))
        raise SystemExit(2) from None
