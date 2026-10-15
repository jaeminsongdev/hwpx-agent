"""One explicit case165/run008 recovery, never reuse run007 as a PASS.

The immutable failed receipt joins the full Native input scope. Only the
product capture deadline is tightened; source IO, CPU/RAM and 600s stay.
"""
from types import FunctionType,SimpleNamespace as NS

RECOVERY_SOURCE="tools/p09/post_product_recovery_connection_v1.py"
RECOVERY_TEST="tools/p09/tests/test_post_product_recovery_connection_v1.py"
RECOVERY_PREFIX="implementation/p09/evidence/p09-361-case165-"
REVIEW_NAME=RECOVERY_PREFIX+"post-product-recovery-review003.v1.json"
REVIEW_STATE="PASS_READ_ONLY_POST_PRODUCT_FAILURE_CLASSIFICATION_NOT_RETRY_DISPATCH_OR_ACCEPTANCE"


def require(ok,label):
    if not ok:raise ValueError("POST_PRODUCT_CONNECTION_"+label)


def clone(fn,**dependencies):
    require(type(fn) is FunctionType,"ORIGINAL_FUNCTION")
    result=FunctionType(fn.__code__,dict(fn.__globals__,**dependencies),argdefs=fn.__defaults__,closure=fn.__closure__)
    result.__kwdefaults__=fn.__kwdefaults__
    return result


def current_window(original,tool,raw):
    """Private full template, actual capture, model and independent predicates."""
    require(original.template.__code__.co_filename.replace("\\","/").endswith(
        "flat_current_queue_product_window_runtime_v18.py"),"ORIGINAL_WHOLE_WINDOW_TEMPLATE")
    component=tool.tighten_window(original.WINDOW,raw)
    native=NS(**{**vars(original.NATIVE),"model":tool.tighten_model(original.NATIVE.model)})
    direct=original.DIRECT
    budget=clone(direct.runtime_budget,views=native)
    mechanics=direct.mechanics_projection
    constants=mechanics.__code__.co_consts
    slots=[i for i,v in enumerate(constants) if type(v) is tuple and v==(20,15)]
    require(len(slots)==1,"ONE_MECHANICS_PRODUCT_EXPECTATION")
    changed=list(constants);changed[slots[0]]=(20,10)
    code=mechanics.__code__.replace(co_consts=tuple(changed));undo=list(code.co_consts);undo[slots[0]]=(20,15)
    require(code.replace(co_consts=tuple(undo))==mechanics.__code__,"FULL_MECHANICS_INVERSE")
    new_mechanics=FunctionType(code,mechanics.__globals__,argdefs=mechanics.__defaults__,closure=mechanics.__closure__)
    new_mechanics.__kwdefaults__=mechanics.__kwdefaults__
    direct=NS(**{**vars(direct),"runtime_budget":budget,"cost":clone(direct.cost,runtime_budget=budget),
        "retained_evidence":clone(direct.retained_evidence,runtime_budget=budget),"mechanics_projection":new_mechanics})
    check=original.WINDOW_LINK.check_evidence
    require(check.__code__.co_filename.replace("\\","/").endswith("strict_product_window_connection_v1.py"),
        "ORIGINAL_COMPLETE_CAPTURE_CHECKER")
    revised=tool.clone(check,tool.code_slots(check,{15:10}))
    link=NS(**{**vars(original.WINDOW_LINK),"check_evidence":revised})
    template=clone(original.template,WINDOW=component,NATIVE=native,DIRECT=direct,WINDOW_LINK=link,
        WINDOW_STATES=[],FORMAT_STATES=[],ATTEMPT_STATES=[])
    return NS(**{**vars(original),"WINDOW":component,"NATIVE":native,"DIRECT":direct,
        "WINDOW_LINK":link,"template":template}),dict(actual_capture_and_cost_and_independent_checker_seconds=10,
        full_original_template_and_capture_code_retained=True,whole_code_inverse_for_timing_expectations=True,
        original_default_and_historical_window15_not_mutated=True,GO_authorized=False,accepted_count_delta=0)


def prior_alias(old,tool,raw):
    window,proof=current_window(old.old.prior,tool,raw)
    return NS(**{**vars(old),"old":NS(**{**vars(old.old),"prior":window})}),proof


def bind_current_prior(namespace,tool,raw):
    """Local imports must resolve the private alias too, not the default module."""
    family_name=getattr(namespace,"__name__",None)
    require(type(family_name) is str and family_name.startswith("p09_exact_"),"PRIVATE_RUNTIME_FAMILY_ONLY")
    seen=set();count=0
    for fn in tuple(vars(namespace).values()):
        if type(fn) is not FunctionType:continue
        env=fn.__globals__
        if id(env) in seen:continue
        seen.add(id(env))
        if env.get("__name__")!=family_name:continue
        previous=fn.__builtins__["__import__"]
        old=previous("case160_run007_controller",env,None,(),0)
        alias,_=prior_alias(old,tool,raw)
        def declared(name,globals=None,locals=None,fromlist=(),level=0,prior=previous,value=alias):
            if level==0 and name=="case160_run007_controller":return value
            return prior(name,globals,locals,fromlist,level)
        env.update(old=alias,__builtins__={**fn.__builtins__,"__import__":declared})
        for name,value in tuple(vars(namespace).items()):
            if type(value) is FunctionType and value.__globals__ is env:
                revised=FunctionType(value.__code__,env,argdefs=value.__defaults__,closure=value.__closure__)
                revised.__kwdefaults__=value.__kwdefaults__
                if env.get(name) is value:env[name]=revised
                setattr(namespace,name,revised)
        count+=1
    require(count==1,"ONE_CURRENT_RUNTIME_OLD_ALIAS")


def receipt_namespace(fn,mapping):
    """Exact metadata literals only, with a complete recursive code inverse."""
    from types import CodeType
    require(type(fn) is FunctionType and type(mapping) is dict and mapping
        and all(type(k) is str and type(v) is str and k!=v for k,v in mapping.items())
        and len(set(mapping.values()))==len(mapping),"EXPLICIT_UNIQUE_RECEIPT_METADATA")
    counts=dict.fromkeys(mapping,0)
    def transform(value,pairs,measure=False):
        if type(value) is CodeType:return value.replace(co_consts=tuple(transform(v,pairs,measure) for v in value.co_consts))
        if type(value) is tuple:return tuple(transform(v,pairs,measure) for v in value)
        if type(value) is str and value in pairs:
            if measure:counts[value]+=1
            return pairs[value]
        return value
    require(transform(fn.__code__,dict.fromkeys(mapping.values(),None))==fn.__code__,"NO_EXISTING_RECOVERY_RECEIPT_LITERAL")
    code=transform(fn.__code__,mapping,True)
    require(all(counts.values()) and transform(code,{v:k for k,v in mapping.items()})==fn.__code__,
        "ENTIRE_RECEIPT_NAMESPACE_CODE_INVERSE")
    result=FunctionType(code,fn.__globals__,argdefs=fn.__defaults__,closure=fn.__closure__)
    result.__kwdefaults__=fn.__kwdefaults__
    return result


def connect_oracle(original,tool,raw):
    def connect(*args,**kwargs):
        checker,proof=original(*args,**kwargs)
        # Preserve the entire scoped/full original checker, including wrappers
        # already installed by the lossless metadata accounting connection.
        env=checker.environment
        require(env["base"].CONFIG.index==165,"CURRENT165_INDEPENDENT_ORACLE_ONLY")
        env["prior"],window_proof=current_window(env["prior"],tool,raw)
        return checker,dict(proof,recovery_window=window_proof)
    return connect


def qualified(q,name,state,a,contracts=None):
    row=q.json(name)
    expected=dict(state=state,cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False)
    if contracts is not None:expected["contracts"]=dict(run=contracts,errors=0,failures=0,skipped=0)
    a.fields(row,expected,"RECOVERY_CLOSED_QUALIFICATION")
    require(type(row["fresh_inputs"]) is int and row["fresh_inputs"]==row["final_fresh_hashes"]>0,
        "ALL_RECOVERY_CLOSING_HASHES")
    for pin in row["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_RECOVERY_QUALIFIED_SOURCES")
    return row


def admit_failed_run(q,ctx,a,reviewer,absent):
    require(type(ctx.index) is int and ctx.index==165 and type(ctx.run) is int and ctx.run==8,
        "ONLY_EXPLICIT165_RUN008")
    future=RECOVERY_PREFIX+"current-runtime-run008.v1.json"
    require(absent(q,future),"NO_EXISTING_NEXT_NATIVE_BEFORE_ADMISSION")
    receipt=qualified(q,REVIEW_NAME,REVIEW_STATE,a)
    raw=q.text(reviewer.CANDIDATE["path"]).encode("utf-8")
    a.exact(q.snapshots[reviewer.CANDIDATE["path"]],reviewer.CANDIDATE,"IMMUTABLE_FAILED_RUN007")
    reviewed=reviewer.review(raw,reviewer.RESPONSE)
    a.fields(receipt,reviewed,"SAME_EXPLICITLY_REVIEWED_FAILURE_NOT_OLD_PASS")
    require(receipt["runtime_retry_admission_implemented"] is False
        and receipt["next_Native_start_authorized"] is False,"REVIEW_NOT_RETRY_OR_GO_AUTHORITY")
    require(absent(q,future),"NO_EXISTING_NEXT_NATIVE_AFTER_ADMISSION")
    return dict(previous_run=7,new_physical_run=8,original_failure_preserved=True,
        raw_failed_receipt_in_current_source_scope=True,old_body_result_reused=False,
        two_new_actual_byte_boundaries_and_complete_oracles_required=True,accepted_count_delta=0,
        GO_authorized=False,queue_advance_authorized=False)
