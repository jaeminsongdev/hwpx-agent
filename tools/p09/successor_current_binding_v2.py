"""Actual160 binding with unchanged full binding and private159 predecessor.

No product body, Native acquisition or acceptance writer is called here.
"""
from types import SimpleNamespace as NS
import isolated_predecessor159_prepare_v1 as predecessor
import current_successor_acceptance_prepare_v1 as adapter
import runtime_successor_binding_v2 as successor
import runtime_successor_manifest_v2 as manifest
import runtime_successor_worker_capsule_v2 as capsule
import successor_runtime_graph_v2 as factory

SELF="tools/p09/successor_current_binding_v2.py"
PRIOR_CODE="implementation/p09/evidence/p09-361-case160-isolated-prior159-code9-r763.v1.json"
GRAPH_CODE="implementation/p09/evidence/p09-361-case160-shared-graph-r759.v1.json"


def previous_callback(controller):
    m=controller.M
    def validate(q,row,listing,oldbody,fresh,ctx,flat=True):
        m.a.require(type(flat) is bool and flat and type(ctx.INDEX) is int and ctx.INDEX==159 and
            type(ctx.BEFORE) is int and ctx.BEFORE==152 and listing["source_test_names"][158]==ctx.CASE,
            "EXACT_WHOLE_PRIOR159_CONTEXT")
        m.a.exact(oldbody,m.a.read_exact(q,m.a.BODY_PIN),"ORIGINAL_PRIOR_BODY_SAME_FRESH_BYTES")
        m.a.exact(fresh,m.a.packed.unpack(m.a.read_exact(q,m.a.FRESH_PIN),q.checkpoint),
            "ORIGINAL_PRIOR_FIXTURE_UNPACK_SAME_FRESH_BYTES")
        verified,verified_listing,evidence,proof=predecessor.prepare(q,controller,adapter,successor)
        m.a.exact(row,verified,"BINDING_ORIGINAL_UNMODIFIED_PRIOR159_ROW")
        m.a.exact(listing,verified_listing,"BINDING_ORIGINAL_COMPILED_ROSTER")
        return evidence,dict(proof,original_binding_previous_callback_checked_actual_full159_oracle=True,
            prior_candidate_row_or_resource_counters_mutated=False,hash_only_predecessor_substitution=False)
    return validate


def bind(q,controller):
    m=controller.M;current=m.base.CONFIG;old=m.old
    m.a.require(current is not None and type(current.index) is int and current.index==160 and
        type(current.before) is int and current.before==153,"EXACT160_FULL_BINDING_CONFIG")
    proof=q.json(PRIOR_CODE)
    m.a.fields(proof,dict(state="PASS_CURRENT160_ISOLATED_PRIOR159_WHOLE_ORACLE_CODE9_NOT_CURRENT160_CONTROLLER_OR_GO",
        contracts=dict(run=9,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
        default_current160_CONFIG_mutated=False),"QUALIFIED160_PRIVATE159_ORACLE")
    for pin in proof["source_pins"]:m.a.exact(q.pin(pin["path"]),pin,"EXACT_QUALIFIED_PRIVATE159_SOURCES")
    for path in (SELF,predecessor.SELF,predecessor.TEST,adapter.SELF,successor.SELF,
                 successor.TEST,manifest.SELF,capsule.SELF,capsule.TEST,factory.SELF):q.pin(path)
    def admit(reader):return successor.admission(reader,m.a,old.failed_role,old.failed004_role)
    once,counts=old.admission_once.connect(admit)
    context=once(q)
    graph=factory.build(q,old,successor,capsule,context=context)
    def shared(reader,api,first,second):
        m.a.require(api is m.a and first is old.failed_role and second is old.failed004_role,
            "EXACT160_SHARED_CONTEXT_DEPENDENCIES")
        return once(reader)
    scoped_successor=NS(**{**vars(successor),"admission":shared})
    step=m.base.load_config(159)
    m.a.exact(q.pin(step.path),step.pin,"EXACT_REAL159_STEP_NOT_CURRENT_SWAP")
    private159,isolation=predecessor.isolate(controller,step)
    manifest_pin=q.pin(manifest.PATH)
    live,inherited,admission=manifest.load(q,manifest_pin,m.a,controller=private159,
        new_module=graph.binding_module,successor=scoped_successor)
    m.a.exact(live.descriptors(),graph.binding.descriptors(),"ACTUAL160_MANIFEST_CAPSULE_TWENTY_FOUR_PAIRS")
    m.a.exact(dict(live.manifest_pin),dict(graph.binding.manifest_pin),"ACTUAL160_MANIFEST_CAPSULE_PIN")
    original=old.prior.M.V3.OLD.API
    pin,raw=q._read(original.BASE_PIN["path"],parse=True);q._bind(pin["path"],pin)
    m.a.exact(pin,original.BASE_PIN,"EXACT_ORIGINAL_WHOLE_BINDING_SOURCE")
    frozen,ast_proof=original.binding_projection(bytes(raw),replacement=previous_callback(controller))
    required,rust=frozen(q)
    complete=m.base.scope.extend(m.base.scope.extend(required,inherited),q.snapshots)
    projection,union_proof=live.project(complete,q.checkpoint)
    m.a.require(len(rust)==787 and projection.semantic_pins.get(m.base.scope.EXE_PIN["path"])==m.base.scope.EXE_PIN,
        "ALL_CURRENT_RUST787_AND_ORIGINAL_COMPILED_EXE")
    m.a.require(m.base.CONFIG is current,"CURRENT160_CONFIG_OBJECT_UNCHANGED_AFTER_FULL159_ORACLE")
    return complete,rust,graph,live,dict(original_binding_AST_proof=ast_proof,
        actual_manifest_admission=admission,complete_scope_union=union_proof,
        private159_isolation=isolation,same_reader_context_declaration_admissions=counts,
        current_CONFIG_mutated=False,original_parent_compiled_Rust_bootstrap_archive_checks_executed=True,
        whole_current160_controller_DATA_import_inventory_preflight_or_GO_qualified=False)
