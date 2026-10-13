"""Whole accepted158 preparation under a private158 configuration facade.

The current CONFIG stays159. Original V25 function bodies, old DATA admission,
manifest and frozen full prepare/oracle are retained. Reconnect only the
same-reader admission wrapper to its privately cloned original callback.
No frame, worker, product replay, queue writer or temporary CONFIG swap.
"""
from types import FunctionType, SimpleNamespace as NS

SELF="tools/p09/isolated_predecessor158_prepare_v1.py"
TEST="tools/p09/tests/test_isolated_predecessor158_prepare_v1.py"
READ_ONLY_QUAL="implementation/p09/evidence/p09-361-case158-current-envelope-full-read-only-prepare-r725.v1.json"


def require(ok,label):
    if not ok:raise ValueError("ISOLATED_PREDECESSOR158_"+label)


def isolate(m,step):
    current=m.base.CONFIG
    require(current is not None and type(current.index) is int and current.index==159 and
        type(current.before) is int and current.before==152,"ONLY_CURRENT159_BEFORE152")
    require(type(step.index) is int and step.index==158 and type(step.before) is int and step.before==151,
        "ONLY_REAL_PRIOR158_BEFORE151")
    family=m.only158.__globals__;env=dict(family);cloned=[]
    for name,fn in family.items():
        if type(fn) is FunctionType and fn.__globals__ is family:
            replacement=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
            replacement.__kwdefaults__=fn.__kwdefaults__
            require(replacement.__code__ is fn.__code__ and replacement.__defaults__ is fn.__defaults__ and
                replacement.__closure__ is fn.__closure__ and replacement.__kwdefaults__ is fn.__kwdefaults__,
                "ALL_ORIGINAL_FUNCTION_CODE_DEFAULTS_CLOSURE_RETAINED")
            env[name]=replacement;cloned.append(name)
    require("_original_own_inputs" in cloned and "validate_candidate" in cloned and "validator" in cloned,
        "WHOLE_OLD_ADMISSION_AND_ORACLE_FAMILY")
    private_base=NS(**{**vars(m.base),"CONFIG":step})
    private_api=NS(**vars(m.API))
    env.update(base=private_base,API=private_api)
    own,counts=m.admission_once.connect(env["_original_own_inputs"])
    env["own_inputs"]=own
    private_api.own_inputs=own
    facade=NS(**env)
    original_projection=m.CURRENT_SOURCE.prepare_projection
    def prepare_projection(raw):
        prepared=original_projection(raw)
        require(type(prepared) is FunctionType and "r" in prepared.__globals__,
            "ORIGINAL_FROZEN_PREPARE_RUNTIME_DEPENDENCY")
        runtime=NS(**{**vars(prepared.__globals__["r"]),"CONFIG":step})
        fn=FunctionType(prepared.__code__,dict(prepared.__globals__,r=runtime),
            argdefs=prepared.__defaults__,closure=prepared.__closure__)
        fn.__kwdefaults__=prepared.__kwdefaults__
        require(fn.__code__ is prepared.__code__,"ENTIRE_FROZEN_PREPARE_CODE_RETAINED")
        return fn
    facade.CURRENT_SOURCE=NS(**{**vars(m.CURRENT_SOURCE),"prepare_projection":prepare_projection})
    env["CURRENT_SOURCE"]=facade.CURRENT_SOURCE
    facade.only158()
    require(m.base.CONFIG is current and facade.base is not m.base,"DEFAULT_CURRENT_CONFIG_UNCHANGED")
    return facade,dict(original_function_family_cloned=sorted(cloned),
        all_original_code_defaults_closure_kwdefaults_retained=True,
        old_complete_admission_wrapper_reconnected_not_bypassed=True,
        original_frozen_prepare_r_CONFIG_privately_bound_to_prior158=True,
        original_current_CONFIG_mutated=False,temporary_CONFIG_swap_used=False,
        actual_product_or_Native_replayed=False,queue_acceptance_called=False)


def prepare(q,m,adapter,successor):
    current=m.base.CONFIG
    require(current is not None and current.index==159 and current.before==152,"EXACT_CURRENT159_CONFIG")
    previous=m.base.load_config(158)
    m.a.exact(q.pin(previous.path),previous.pin,"REAL_IMMUTABLE_PRIOR158_STEP")
    authority=m.a.read_exact(q,successor.AUTHORITY)
    m.a.fields(authority,dict(state="PASS_EXACT_FLAT_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE",
        accepted_count_after=152,accepted_count_delta=1,next_runtime_index=159,
        runtime_candidate_pin=successor.ROOT,resource_cleanup_confirmed=True,P09_gate="OPEN"),
        "EXACT_ACTUAL152_AUTHORITY_AND_ROOT158")
    qualified=q.json(READ_ONLY_QUAL)
    m.a.fields(qualified,dict(state="PASS_CURRENT_ENVELOPE_FULL_READ_ONLY_PREPARE_NOT_QUEUE_ACCEPTANCE",
        runtime_pin=successor.ROOT,product_or_Native_reexecuted=False,queue_acceptance_called=False,
        cleanup_confirmed=True),"ORIGINAL_QUALIFIED_WHOLE158_PREPARE")
    for pin in qualified["source_pins"]:m.a.exact(q.pin(pin["path"]),pin,"UNCHANGED_QUALIFIED_WHOLE158_PREPARE_SOURCES")
    facade,proof=isolate(m,previous)
    original_binding=m._binding;original_checkpoint=m._checkpoint
    row,listing,evidence,oracle=adapter.prepare(q,successor.ROOT,facade)
    require(m.base.CONFIG is current and m._binding is original_binding and m._checkpoint is original_checkpoint,
        "DEFAULT159_CONFIG_BINDING_CHECKPOINT_UNCHANGED")
    m.a.fields(row,dict(selected_test_index=158,current_generation_runtime_candidate_qualified=True,
        cleanup_confirmed=True,owned_tree_empty=True),"EXACT_PRIOR_ACTUAL158_NOT_REPLAY159")
    m.a.fields(row["source_frame"],dict(frame_state="COMMITTED",registered_live_frame=False,
        original_two_actual_per_case_byte_reads_retained=True),"WHOLE_ACTUAL158_FRAME")
    require(len(row["source_frame"]["actual_byte_boundaries"])==2,"BOTH_ORIGINAL158_BOUNDARIES")
    return row,listing,evidence,dict(proof,whole_original_prior158_oracle=oracle,
        real_prior_step_pin=previous.pin,actual_prior_runtime_pin=successor.ROOT,
        actual_current159_controller_or_GO_qualified=False)
