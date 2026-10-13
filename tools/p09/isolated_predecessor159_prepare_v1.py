"""Whole original159 oracle under private159 while current CONFIG stays160.

Clone the exact original function family, reconnect unchanged full admission
and frozen prepare dependencies. No temporary default CONFIG swap or runtime
replay, no observed frame rewrite and no queue writer.
"""
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/isolated_predecessor159_prepare_v1.py"
TEST="tools/p09/tests/test_isolated_predecessor159_prepare_v1.py"
QUAL="implementation/p09/evidence/p09-361-case159-successor-full-prepare-r751.v1.json"


def require(ok,label):
    if not ok:raise ValueError("ISOLATED_PRIOR159_"+label)


def isolate(controller,step):
    m=controller.M;current=m.base.CONFIG
    require(current is not None and type(current.index) is int and current.index==160 and
        type(current.before) is int and current.before==153,"ONLY_CURRENT160_BEFORE153")
    require(type(step.index) is int and step.index==159 and type(step.before) is int and step.before==152,
        "ONLY_REAL_PRIOR159_BEFORE152")
    family=m.only159.__globals__;env=dict(family);cloned=[]
    for name,fn in family.items():
        if type(fn) is FunctionType and fn.__globals__ is family:
            replacement=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
            replacement.__kwdefaults__=fn.__kwdefaults__;env[name]=replacement;cloned.append(name)
    require(all(name in cloned for name in ("_original_own_inputs","only159","graph_value","validator","validate_candidate")),
        "WHOLE_ORIGINAL159_ADMISSION_GRAPH_AND_ORACLE_FAMILY")
    private_base=NS(**{**vars(m.base),"CONFIG":step})
    private_api=NS(**vars(m.API))
    # Original159 admission passes its old dependency to the current-binding
    # qualifier; bind that dependency's CONFIG privately as well.
    private_old=NS(**{**vars(m.old),"base":private_base})
    env.update(base=private_base,API=private_api,old=private_old)
    raw_own=env["_original_own_inputs"]
    def own(reader):
        for pin in controller.RAW_PINS+[controller.RAW_TEST_PIN]:
            m.a.exact(reader.pin(pin["path"]),pin,"ALL_ORIGINAL159_RAW_SOURCE_INPUTS")
        reader.pin(m.SELF);reader.pin(m.TEST)
        return raw_own(reader)
    owned,counts=m.old.admission_once.connect(own)
    env["own_inputs"]=owned;private_api.own_inputs=owned
    facade=NS(**env)
    original_projection=m.CURRENT_SOURCE.prepare_projection
    def prepare_projection(raw):
        prepared=original_projection(raw)
        require(type(prepared) is FunctionType and "r" in prepared.__globals__,"ORIGINAL_FROZEN159_PREPARE_DEPENDENCY")
        runtime=NS(**{**vars(prepared.__globals__["r"]),"CONFIG":step})
        result=FunctionType(prepared.__code__,dict(prepared.__globals__,r=runtime),
            argdefs=prepared.__defaults__,closure=prepared.__closure__)
        result.__kwdefaults__=prepared.__kwdefaults__
        require(result.__code__ is prepared.__code__,"ENTIRE_ORIGINAL_FROZEN_PREPARE_CODE")
        return result
    facade.CURRENT_SOURCE=NS(**{**vars(m.CURRENT_SOURCE),"prepare_projection":prepare_projection})
    env["CURRENT_SOURCE"]=facade.CURRENT_SOURCE
    facade.only159()
    require(m.base.CONFIG is current,"DEFAULT160_CONFIG_UNCHANGED")
    return facade,dict(original_function_family_cloned=sorted(cloned),
        original_function_code_defaults_closure_kwdefaults_retained=True,
        unchanged_full_raw_admission_reconnected=True,temporary_CONFIG_swap=False,
        default160_config_mutated=False,current159_runtime_replayed=False,queue_acceptance_called=False)


def prepare(q,controller,adapter,successor):
    m=controller.M;current=m.base.CONFIG
    require(current is not None and current.index==160 and current.before==153,"CURRENT160_REQUIRED")
    step=m.base.load_config(159)
    m.a.exact(q.pin(step.path),step.pin,"REAL_IMMUTABLE_PRIOR159_STEP")
    authority=m.a.read_exact(q,successor.AUTHORITY)
    m.a.fields(authority,dict(state="PASS_EXACT_FLAT_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE",
        accepted_count_after=153,next_runtime_index=160,runtime_candidate_pin=successor.ROOT,
        resource_cleanup_confirmed=True,P09_gate="OPEN"),"EXACT_AUTHORITY153_ROOT159")
    qualified=q.json(QUAL)
    m.a.fields(qualified,dict(state="PASS_CURRENT159_SUCCESSOR_FULL_READ_ONLY_PREPARE_NOT_QUEUE_ACCEPTANCE",
        runtime_pin=successor.ROOT,product_or_Native_reexecuted=False,queue_acceptance_called=False,
        cleanup_confirmed=True),"QUALIFIED_WHOLE_ORIGINAL159_PREPARE")
    for pin in qualified["source_pins"]:m.a.exact(q.pin(pin["path"]),pin,"EXACT_QUALIFIED159_PREPARE_SOURCES")
    facade,proof=isolate(controller,step)
    original_env=m.only159.__globals__;graph_before=original_env["_graph"];checkpoint_before=original_env["_checkpoint"]
    row,listing,evidence,oracle=adapter.prepare(q,successor.ROOT,facade)
    require(m.base.CONFIG is current and original_env["_graph"] is graph_before and
        original_env["_checkpoint"] is checkpoint_before,"DEFAULT160_CONFIG_GRAPH_CHECKPOINT_UNCHANGED")
    m.a.fields(row,dict(selected_test_index=159,current_generation_runtime_candidate_qualified=True,
        cleanup_confirmed=True,owned_tree_empty=True),"EXACT_PRIOR159_NOT_CURRENT160")
    m.a.fields(row["source_frame"],dict(frame_state="COMMITTED",registered_live_frame=False,
        original_two_actual_per_case_byte_reads_retained=True),"ORIGINAL_WHOLE_PRIOR159_FRAME")
    require(len(row["source_frame"]["actual_byte_boundaries"])==2,"BOTH_ORIGINAL159_BYTE_BOUNDARIES")
    return row,listing,evidence,dict(proof,whole_original159_oracle=oracle,prior_step_pin=step.pin,
        prior_runtime_pin=successor.ROOT,current160_controller_scope_preflight_or_GO_qualified=False)
