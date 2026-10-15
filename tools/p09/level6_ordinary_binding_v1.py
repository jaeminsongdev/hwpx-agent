"""Pinned ordinary recompression policy on the complete private Binding.

Keep all 68 logical inputs and the seven old failure/closed-prebody physical
pins. No Native/GO/queue writer. Worker uses a code-pinned table digest, not a
claim of parent admission; all original byte/lock/oracle methods remain.
"""
from pathlib import Path
from types import SimpleNamespace as NS
from contextlib import contextmanager, ExitStack
import hashlib
import json
import re
import sys

SELF = "tools/p09/level6_ordinary_binding_v1.py"
TEST = "tools/p09/tests/test_level6_ordinary_binding_v1.py"
SPEC = dict(index=165, count=61, mapping_sha256="519e89382d5e1032324a6378394e8913ca2d51eb97fe6c6445b382404870d9ad")
PROOF = dict(path="implementation/p09/evidence/p09-361-case165-level6-corpus-verification001.v1.json",
    bytes=31104, sha256="6ab58fe2438272cd54ff2b6f37af04e24a6aab894748d547c13a15790dc47da0")
FRONT = dict(path="tools/p09/expanded_closed_preparation_v1.py", bytes=21675,
    sha256="8de7dc45657401ceefc05a8535114155da138f79d3d17a9c6f2491808e43fca1")
BINDINGS = dict(path="tools/p09/current_queue_successor_binding.py", bytes=15040,
    sha256="6d48c8df7a085461bdad22f8ee4be2baa9675f8035b558f7bc3474b52ea6e915")
PREFIX = "implementation/p09/evidence/p09-361-case165-"


def require(ok, code):
    if not ok: raise ValueError("LEVEL6_ORDINARY_BINDING_" + code)


def fingerprint(rows):
    return hashlib.sha256(json.dumps(rows, ensure_ascii=True, sort_keys=True,
        allow_nan=False, separators=(",", ":")).encode("ascii")).hexdigest()


def is_new(row):
    return row["physical_envelope_pin"]["path"].endswith(".level6.envelope.v1.json")


def choose(baseline, proposed, spec=SPEC):
    require(type(baseline) is list and type(proposed) is list and len(baseline) == len(proposed) == 68, "COMPLETE68")
    rows = []
    for old, new in zip(baseline, proposed):
        require(set(old) == set(new) == {"schema_version", "next_case", "semantic_original_pin", "physical_envelope_pin"}, "CLOSED_ROWS")
        require({k:v for k,v in old.items() if k != "physical_envelope_pin"}
            == {k:v for k,v in new.items() if k != "physical_envelope_pin"}, "EVERY_LOGICAL_INPUT_UNCHANGED")
        preserve = ".failed." in old["physical_envelope_pin"]["path"] or f"case{spec['index']}-" in old["semantic_original_pin"]["path"]
        rows.append(old if preserve else new)
    selected = [r for r in rows if is_new(r)]
    require(len(selected) == spec["count"] and fingerprint(selected) == spec["mapping_sha256"], "INDEPENDENT_EXPECTED_TABLE_DIGEST")
    return rows


def admit(q, a, scope):
    """Fresh mapping/source metadata only; Native physical reads stay mandatory."""
    proof = a.read_exact(q, PROOF)
    a.fields(proof, dict(state="PASS_FULL68_LEVEL6_CORPUS_AND_DECLARED_COST_NOT_CURRENT_ENTRY_OR_RUNTIME",
        pair_count=68, fresh_inputs=94, final_fresh_hashes=94, cleanup_confirmed=True,
        product_or_Native_executed=False, accepted_count_delta=0), "QUALIFIED_FULL_CORPUS")
    a.fields(proof["decoder_budget"], dict(aggregate_limit_seconds=5.0, attempted_decodes=136,
        completed_decodes=136, active_decode=False, terminal_error_seen=False), "CORPUS_TWO_FRESH_DECODES")
    for pin in proof["source_pins"]:
        if pin["path"].startswith("tools/p09/") and pin["path"].endswith(".py"):
            a.exact(q.pin(pin["path"]), pin, "CURRENT_CORPUS_SOURCE")
    current = a.read_exact(q, proof["diagnostic_manifest_pin"])
    baseline = a.read_exact(q, current["baseline_manifest_pin"])
    rows = choose(baseline["descriptors"], current["descriptors"])
    scope.pins([r["semantic_original_pin"] for r in rows])
    scope.pins([r["physical_envelope_pin"] for r in rows])
    return baseline, rows, dict(SPEC)


def install(module, historical_pairs, spec=SPEC):
    """Whole old constructor, original special predicates and all byte oracles."""
    source = module.source; env = source.Projection.__init__.__globals__
    require(env.get("__name__", "").startswith("p09_exact_runtime_envelope_source_projection_v1") and not any(
        getattr(m, "__dict__", None) is env for m in tuple(sys.modules.values()) if m), "PRIVATE_NAMESPACE_ONLY")
    require(type(spec) is dict and set(spec) == {"index", "count", "mapping_sha256"}
        and type(spec["index"]) is int and spec["index"] == 165
        and type(spec["count"]) is int and spec["count"] == 61
        and re.fullmatch(r"[0-9a-f]{64}", spec["mapping_sha256"]) is not None, "EXACT_PROFILE_CONTEXT")
    if hasattr(module, "level6_ordinary_profile"):
        module.exact(module.level6_ordinary_profile, spec, "ONE_PROFILE_PER_PRIVATE_MODULE")
        return
    inherited = {r["semantic_original_pin"]["path"]: r for r in historical_pairs}
    original = source.descriptor; initialize = module.Binding.__init__
    methods = {n:fn for n,fn in vars(module.Binding).items() if n != "__init__"}
    def descriptor(old, new, *, next_case):
        if type(new) is not dict or not str(new.get("path", "")).endswith(".level6.envelope.v1.json"):
            return original(old, new, next_case=next_case)
        old = source.copy_pin(old); new = source.copy_pin(new)
        match = re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-current-runtime-run([0-9]{3})\.v1\.json", old["path"])
        require(type(next_case) is int and next_case == spec["index"] and match is not None
            and 112 <= int(match[1]) < next_case, "ORDINARY_PRIOR_NOT_CURRENT")
        name = source.PREFIX + f"case{match[1]}-runtime-run{match[2]}"
        require(new["path"] == name + ".level6.envelope.v1.json", "NO_FAILED_OR_ARBITRARY_NEW_PATH")
        prior = inherited.get(old["path"])
        before = dict(prior["physical_envelope_pin"]) if prior is not None else dict(new, path=name + ".envelope.v1.json")
        require(".failed." not in before["path"], "FAILED_INHERITANCE_RETAINED")
        # This validates historical identity, not a claim that before was read.
        expected = original(old, before, next_case=next_case)
        require(0 < new["bytes"] <= source.codec.MAX_BYTES, "UNCHANGED_PHYSICAL_PARSE_BOUND")
        return dict(expected, physical_envelope_pin=new)
    def init(self, descriptors, manifest_pin, *, next_case):
        initialize(self, descriptors, manifest_pin, next_case=next_case)
        selected = [r for r in self.descriptors() if is_new(r)]
        if selected:
            observed = fingerprint(selected)
            if not (len(self.descriptors()) == 68 and len(selected) == spec["count"] and observed == spec["mapping_sha256"]):
                raise ValueError("LEVEL6_ORDINARY_BINDING_WHOLE61_EXACT_CODE_PINNED_TABLE",
                    dict(rows=len(self.descriptors()), new_rows=len(selected), observed_sha256=observed, expected_sha256=spec["mapping_sha256"]))
    source.descriptor = descriptor; env["descriptor"] = descriptor
    module.Binding.__init__ = init; module.level6_ordinary_profile = dict(spec)
    module.level6_original_initialize = initialize
    require(all(vars(module.Binding).get(n) is fn for n,fn in methods.items()), "ALL_ORIGINAL_NONCONSTRUCTOR_METHODS")


@contextmanager
def bootstrap_seed(module, expected, manifest_pin):
    """One original metadata-only seed; every later constructor stays full61.

    Scope this around the unmodified original reconstruction, not around an
    execution callback. Its first one-row graph only creates the decoder; the
    original decoder must then produce the entire 68-row binding.
    """
    require(hasattr(module, "level6_original_initialize"), "PROFILE_REQUIRED_BEFORE_SEED")
    previous = module.Binding.__init__; state = dict(used=False)
    def initialize(self, descriptors, pin, *, next_case):
        if not state["used"]:
            module.exact(descriptors, [expected], "EXACT_ORIGINAL_BOOTSTRAP_FIRST_DESCRIPTOR")
            module.exact(pin, manifest_pin, "EXACT_ORIGINAL_BOOTSTRAP_MANIFEST")
            state["used"] = True
            return module.level6_original_initialize(self, descriptors, pin, next_case=next_case)
        return previous(self, descriptors, pin, next_case=next_case)
    module.Binding.__init__ = initialize
    try:
        yield state
        require(state["used"], "ORIGINAL_SEED_MUST_ACTUALLY_RUN")
    finally:
        require(module.Binding.__init__ is initialize, "ONE_SCOPED_SEED_OWNER")
        module.Binding.__init__ = previous


def main():
    import argparse, io, time, unittest
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    parser = argparse.ArgumentParser(); parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--code-attempt", type=int, default=5)
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args(); require(1 <= args.attempt <= 8, "ATTEMPT")
    name = PREFIX + f"level6-binding-{'transport' if args.probe else 'code'}{args.attempt:03}.v1.json"
    require(not (c.ROOT/name).exists(), "EXCLUSIVE_REPORT")
    front_ns,_ = envelope.namespace_bundle.load(c.ROOT, [FRONT], {})
    front = front_ns.expanded_closed_preparation_v1
    namespace, private, proxy, routed = front.components(c.ROOT, envelope)
    utils,_ = envelope.namespace_bundle.load(c.ROOT, private.PINS, {})
    guard = utils.terminal_metadata_pressure_v1.guard_type(utils.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started = time.monotonic(); q = None
    row = dict(state="FAILED_LEVEL6_BINDING_NOT_ADOPTED", product_or_Native_executed=False,
        accepted_count_delta=0, actual_parent_worker_entry_and_independent_review_NOT_RUN=True)
    try:
        guard.acquire(); q = a.AcceptanceReader(c.ROOT, guard.check)
        for path in (SELF, TEST): q.pin(path)
        for pin in (FRONT, BINDINGS): a.exact(q.pin(pin["path"]), pin, "FROZEN_COMPONENTS")
        names,_ = envelope.namespace_bundle.load(c.ROOT, [BINDINGS], {})
        bindings = names.current_queue_successor_binding
        for pin in bindings.PINS: a.exact(q.pin(pin["path"]), pin, "ORIGINAL_BINDING_AND_CODEC")
        if not args.probe:
            tests,_ = envelope.namespace_bundle.load(c.ROOT, [q.snapshots[TEST]], {})
            tests.test_level6_ordinary_binding_v1.Tests.data.__globals__.update(MODULE=sys.modules[__name__], BINDINGS_API=bindings,
                ROOT=c.ROOT, LOADER=envelope.namespace_bundle, SCOPE=scope, CHECKPOINT=guard.check)
            result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
                unittest.defaultTestLoader.loadTestsFromModule(tests.test_level6_ordinary_binding_v1))
            contracts = dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped))
            row["contracts"] = contracts
            row["contract_error_types"] = [dict(test=t.id().rsplit(".",1)[-1],
                exception_type=trace.splitlines()[-1].split(":",1)[0]) for t,trace in result.errors]
            a.exact(contracts, dict(run=10, errors=0, failures=0, skipped=0), "ALL_BINDING10")
            row["state"] = "PASS_LEVEL6_ORDINARY_BINDING_CODE10_NOT_ENTRY_OR_PRODUCT"
        else:
            require(1 <= args.code_attempt <= 8, "CODE_ATTEMPT")
            code = q.json(PREFIX + f"level6-binding-code{args.code_attempt:03}.v1.json")
            a.fields(code, dict(state="PASS_LEVEL6_ORDINARY_BINDING_CODE10_NOT_ENTRY_OR_PRODUCT",
                contracts=dict(run=10, errors=0, failures=0, skipped=0), cleanup_confirmed=True), "MANDATORY_BINDING_CODE10")
            for pin in code["source_pins"]: a.exact(q.pin(pin["path"]), pin, "CURRENT_BINDING_CODE")
            baseline, rows, spec = admit(q, a, scope)
            ctx = NS(preflight=PREFIX+"successor-preflight-run005-attempt001.v1.json",
                qualification=PREFIX+"successor-dispatch-qualification-run005-attempt001.v1.json")
            sources,_ = proxy.namespace_bundle.load(c.ROOT, [front.FIX], {})
            linked = sources.closed_prebody_factory_admission_fix_v1.load(c.ROOT, a, scope, bytes_policy,
                proxy, PREFIX+"sealed-metadata-code001.v1.json", ctx=ctx)
            # Actual reader admits the original closed source policy unchanged.
            admitted = linked.api.AcceptanceReader(c.ROOT, guard.check)
            for pin in q.snapshots.values(): a.exact(admitted.pin(pin["path"]), pin, "ALL_NEW_SOURCES_IN_REAL_READER")
            q = admitted
            base_graph = q.json(PREFIX+"successor-connections004.v9.json")
            step = base_graph["step"]
            prior = a.read_exact(q, step["prior_candidate_pin"])
            historical = prior["source_input_representation"]["descriptors"]
            actual = linked.modules.current_queue_successor_binding
            api = linked.connection.binding_api(actual, linked.alias, q.closed_source_policy)
            module, proof = api.connect(c.ROOT, proxy.namespace_bundle, scope, 165,
                baseline["historical_predecessor_provenance"], historical)
            install(module, historical, spec)
            manifest = dict(baseline, descriptors=rows, ordinary_recompression_spec=spec,
                ordinary_recompression_proof_pin=PROOF, diagnostic_only_not_runtime_adoption=True)
            manifest_name = PREFIX + f"successor-level6-probe-manifest{args.attempt:03}.v1.json"
            manifest_pin = utils.successor_preparation_workspace_v1.publish(c.ROOT, manifest_name, manifest, a)
            a.exact(q.pin(manifest_name), manifest_pin, "ACTUAL_DIAGNOSTIC_MANIFEST")
            bound = module.Binding(rows, manifest_pin, next_case=165)
            row["last_completed_stage"] = "parent_binding"
            runtime = linked.modules.current_queue_successor_runtime
            graph, connected = runtime.metadata.connect(c.ROOT, proxy.namespace_bundle, bytes_policy, module, bound, step, 5, guard.check)
            wire, wire_info = graph.worker.encode(bound, step["prior_queue_pin"], step["prior_candidate_pin"], guard.check)
            row["last_completed_stage"] = "parent_graph_and_wire"
            require(len(wire) <= 16384, "ORIGINAL_WIRE16K")
            capsule_pin = dict(path=PREFIX+"successor-worker-capsule005.compact.v9.json", bytes=len(wire), sha256=hashlib.sha256(wire).hexdigest())
            hint = runtime.worker_hint(step, 5, capsule_pin, manifest_pin, manifest, historical)
            whole = actual.connect
            def connect(*items, **options):
                other, result = whole(*items, **options)
                install(other, historical, spec)
                seed_stack.enter_context(bootstrap_seed(other, hint["first_descriptor"], hint["manifest_pin"]))
                return other, result
            actual.connect = connect
            try:
                with ExitStack() as seed_stack:
                    restored, transport = runtime.reconstruct_worker_graph(c.ROOT, proxy.namespace_bundle, scope, bytes_policy, hint, wire, guard.check)
                    row["last_completed_stage"] = "actual_worker_reconstruction"
            finally: actual.connect = whole
            a.exact(restored.binding.descriptors(), bound.descriptors(), "ALL68_REAL_WORKER_ROWS")
            required = scope.pins([r["semantic_original_pin"] for r in rows]+[manifest_pin])
            parent_projection,_ = bound.project(required, guard.check)
            worker_projection,_ = restored.binding.project(required, guard.check)
            a.exact(bound.representation(parent_projection), restored.binding.representation(worker_projection), "PARENT_WORKER_ALL_ORIGINAL_REPRESENTATION_FIELDS")
            require(graph.parent.access.source is module and graph.frames.binding_module is module
                and graph.worker.source is module and graph.full_oracle.binding_module is module, "SAME_PARENT_FRAME_WORKER_FULL_ORACLE_NAMESPACE")
            row.update(state="PASS_LEVEL6_REAL68_TRANSPORT_AND_ORACLE_NAMESPACE_NOT_ENTRY_OR_PRODUCT", pair_count=68,
                new_ordinary_count=61, preserved_special_count=7, wire_bytes=len(wire), declared_bootstrap_bytes=len((json.dumps(hint,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("ascii")),
                diagnostic_manifest_pin=manifest_pin, capsule_and_bootstrap_not_published=True, current_runtime_root_not_created=True,
                all_nonconstructor_binding_oracles_retained=True, original_raw_and_existing_derivatives_unchanged=True,
                original_single_metadata_seed_scoped_before_full68_decode=True,
                transport=transport, one_private_namespace=connected["one_private_binding_namespace"])
        q.finish(); guard.check(force=True)
        row.update(source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"] = type(error).__name__
        if len(error.args) == 2 and error.args[0] == "LEVEL6_ORDINARY_BINDING_WHOLE61_EXACT_CODE_PINNED_TABLE":
            row["profile_table_observation"] = error.args[1]
        if q is not None: row.update(source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]): row["error_code"] = error.args[0]
    finally:
        guard.close(); row.update(cleanup_confirmed=guard.cleanup, elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None), RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup, "CLEANUP"); utils.successor_preparation_workspace_v1.publish(c.ROOT,name,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","pair_count","new_ordinary_count","preserved_special_count","wire_bytes",
        "fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code","error_type")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__ == "__main__": raise SystemExit(main())
