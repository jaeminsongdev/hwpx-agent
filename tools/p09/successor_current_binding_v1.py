"""Actual159 original full binding plus isolated whole158 predecessor oracle.

Keep the exact frozen binding AST and compiled Rust787/bootstrap/authority
checks. Compose independently admitted semantic scope with actual physical
receipt pairs, never derive expectations from candidate frame observations.
This helper alone is not a complete controller, preflight or GO qualification.
"""
import isolated_predecessor158_prepare_v1 as predecessor
import current_envelope_acceptance_prepare_v1 as prepare_adapter
import runtime_successor_binding_v1 as successor
import runtime_successor_manifest_v1 as manifest
import runtime_successor_worker_capsule_v1 as capsule
import successor_runtime_graph_v1 as graph_factory

SELF="tools/p09/successor_current_binding_v1.py"
TEST="tools/p09/tests/test_successor_current_binding_v1.py"
PRIOR_CODE="implementation/p09/evidence/p09-361-case159-isolated-prior158-code9-r743.v1.json"
GRAPH_CODE="implementation/p09/evidence/p09-361-case159-full-graph-window-code21-r738.v1.json"


def qualify(q,m):
    m.a.require(m.base.CONFIG is not None and type(m.base.CONFIG.index) is int and m.base.CONFIG.index==159
        and type(m.base.CONFIG.before) is int and m.base.CONFIG.before==152,"EXACT159_CURRENT_BINDING_CONFIG")
    for path,state,count in (
        (PRIOR_CODE,"PASS_CURRENT159_ISOLATED_PRIOR158_WHOLE_ORACLE_CODE9_NOT_CURRENT159_CONTROLLER_OR_GO",9),
        (GRAPH_CODE,"PASS_SUCCESSOR159_FULL_MANIFEST_SHARED_GRAPH_AND_WINDOW_CODE21_NOT_CURRENT_CONTROLLER_NATIVE_OR_GO",21)):
        proof=q.json(path)
        m.a.fields(proof,dict(state=state,contracts=dict(run=count,errors=0,failures=0,skipped=0),
            accepted_count_delta=0,actual159_GO_authorized=False,cleanup_confirmed=True),"EXACT_SUCCESSOR_DEPENDENCY_NOT_PRODUCT")
        for pin in proof["source_pins"]:m.a.exact(q.pin(pin["path"]),pin,"CURRENT_FULL_BINDING_QUALIFIED_SOURCES")
    for path in (SELF,TEST,predecessor.SELF,predecessor.TEST,prepare_adapter.SELF,successor.SELF,
                 successor.TEST,manifest.SELF,manifest.TEST,capsule.SELF,capsule.TEST,graph_factory.SELF):q.pin(path)


def previous_callback(m):
    def validate(q,row,listing,oldbody,fresh,ctx,flat=True):
        m.a.require(type(flat) is bool and flat and type(ctx.INDEX) is int and ctx.INDEX==158 and
            type(ctx.BEFORE) is int and ctx.BEFORE==151 and
            listing["source_test_names"][157]==ctx.CASE,"EXACT_WHOLE_PRIOR158_CONTEXT")
        m.a.exact(oldbody,m.a.read_exact(q,m.a.BODY_PIN),"ORIGINAL_PRIOR_BODY_SAME_FRESH_BYTES")
        m.a.exact(fresh,m.a.packed.unpack(m.a.read_exact(q,m.a.FRESH_PIN),q.checkpoint),
            "ORIGINAL_PRIOR_FIXTURE_UNPACK_SAME_FRESH_BYTES")
        verified,verified_listing,evidence,proof=predecessor.prepare(q,m,prepare_adapter,successor)
        m.a.exact(row,verified,"BINDING_ORIGINAL_UNMODIFIED_PRIOR158_ROW")
        m.a.exact(listing,verified_listing,"BINDING_ORIGINAL_COMPILED_ROSTER")
        return evidence,dict(proof,original_binding_previous_callback_checked_actual_full158_oracle=True,
            prior_candidate_row_or_resource_counters_mutated=False,hash_only_predecessor_substitution=False)
    return validate


def bind(q,m):
    qualify(q,m)
    graph=graph_factory.build(q,m,successor,capsule)
    manifest_pin=q.pin(manifest.PATH)
    live,inherited,admission=manifest.load(q,manifest_pin,m.a,old_manifest=m.manifest,
        new_module=graph.binding_module,successor=successor,failed003=m.failed_role,failed004=m.failed004_role)
    m.a.exact(live.descriptors(),graph.binding.descriptors(),"ACTUAL159_MANIFEST_AND_CAPSULE_TWENTY_PAIRS")
    m.a.exact(dict(live.manifest_pin),dict(graph.binding.manifest_pin),"ACTUAL159_MANIFEST_AND_CAPSULE_PIN")
    original=m.prior.M.V3.OLD.API
    pin,raw=q._read(original.BASE_PIN["path"],parse=True);q._bind(pin["path"],pin)
    m.a.exact(pin,original.BASE_PIN,"EXACT_ORIGINAL_WHOLE_BINDING_SOURCE")
    callback=previous_callback(m)
    frozen,ast_proof=original.binding_projection(bytes(raw),replacement=callback)
    required,rust=frozen(q)
    complete=m.base.scope.extend(m.base.scope.extend(required,inherited),q.snapshots)
    projection,union_proof=live.project(complete,q.checkpoint)
    m.a.require(len(rust)==787 and projection.semantic_pins.get(m.base.scope.EXE_PIN["path"])==m.base.scope.EXE_PIN,
        "ALL_CURRENT_RUST787_AND_ORIGINAL_COMPILED_EXE")
    m.a.require(m.base.CONFIG.index==159 and m.base.CONFIG.before==152,"CURRENT_CONFIG_UNCHANGED_AFTER_FULL_PRIOR_ORACLE")
    return complete,rust,graph,live,dict(original_binding_AST_proof=ast_proof,actual_manifest_admission=admission,
        complete_scope_union=union_proof,current_CONFIG_mutated=False,
        original_parent_compiled_Rust_bootstrap_archive_checks_executed=True,
        whole_current_controller_DATA_import_inventory_preflight_or_GO_qualified=False)
