"""Version dispatch for original additional observer check, no record relabel.

원 observer checker bytecode/default/closure와 cost/probe/cleanup/acquisition
guard predicates를 보존한다. original.fields dependency에서 ONE diagnostic
predicate만 native 형식의 더 엄격한 validator로 바꾼다. Default modules intact.
"""
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/native_additional_observer_connection_v1.py"
TEST="tools/p09/tests/test_native_additional_observer_connection_v1.py"


def require(ok,code):
    if not ok:raise ValueError("NATIVE_ADDITIONAL_OBSERVER_"+code)


def dispatch(original,row,diagnostic):
    index=row.get("selected_test_index")
    require(type(index) is int and 115<=index<=249,"EXACT_RECORDED_INDEX")
    if index<=146:
        require(row["serial_CPU_attribution"].get("backend") is None,"HISTORICAL_FORMAT_NOT_REBASED")
        return original(row)
    require(row["serial_CPU_attribution"].get("backend")==diagnostic.BACKEND,"NATIVE147_PLUS_REQUIRED")
    base=original.__globals__["original"]
    old_fields=base.fields;state=dict(diagnostic_changes=0,preserved_field_checks=[])
    def fields(data,expected,code):
        if code=="ONE_ORIGINAL_OBSERVER":
            require(data is row["serial_CPU_attribution"],"SAME_ACTUAL_RECORD_DIAGNOSTIC")
            require(state["diagnostic_changes"]==0,"ONE_DIAGNOSTIC_PREDICATE")
            diagnostic.validate(row)
            state["diagnostic_changes"]+=1
            return
        state["preserved_field_checks"].append(code)
        return old_fields(data,expected,code)
    private=NS(**{**vars(base),"fields":fields})
    fn=FunctionType(original.__code__,dict(original.__globals__,original=private),
                    argdefs=original.__defaults__,closure=original.__closure__)
    require(fn.__code__ is original.__code__ and fn.__defaults__ is original.__defaults__
            and fn.__closure__ is original.__closure__,"ALL_OBSERVER_BYTECODE_RETAINED")
    fn(row)
    require(state["diagnostic_changes"]==1 and state["preserved_field_checks"]==
      ["PDH_COST_NOT_OMITTED","PDH_QUERY_CLEANUP","NEW_ACQUISITION_GUARD"],
      "ALL_ORIGINAL_NONFORMAT_CHECKS_UNCHANGED")
    return dict(one_explicit_native_format_predicate=True,original_observer_bytecode_retained=True,
     cost_probe_cleanup_and_acquisition_guards_retained=True,original_record_or_default_modules_mutated=False)


def connect_projection(function,diagnostic):
    def project(raw):
        fn=function(raw)
        old=fn.__globals__.get("additional_observer_evidence")
        require(type(old) is FunctionType,"EXACT_ORIGINAL_ADDITIONAL_OBSERVER_DEPENDENCY")
        env=dict(fn.__globals__,additional_observer_evidence=lambda row:dispatch(old,row,diagnostic))
        require(set(env)==set(fn.__globals__) and all(env[name] is value for name,value in fn.__globals__.items()
          if name!="additional_observer_evidence"),"ONLY_ONE_ADDITIONAL_OBSERVER_LEAF")
        return FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
    return project


def connect_retained(original_candidate,direct_oracle,diagnostic):
    original=original_candidate.original
    check=original.additional_observer_evidence
    private=NS(**{**vars(original),"additional_observer_evidence":lambda row:dispatch(check,row,diagnostic)})
    candidate=NS(**{**vars(original_candidate),"original":private})
    return lambda row:direct_oracle.retained_evidence(row,candidate)


def connect_candidate(function,original_candidate,direct_oracle,diagnostic):
    state=dict(cloned_functions=[],retained_leaf_changes=0)
    def clone(fn,depth=0):
        require(type(fn) is FunctionType and depth<=12,"BOUNDED_FULL_CANDIDATE_CHAIN")
        env=dict(fn.__globals__)
        for key in ("prior","accepted","metadata","original"):
            obj=env.get(key);child=getattr(obj,"validate_candidate",None)
            if key in fn.__code__.co_names and type(child) is FunctionType:
                env[key]=NS(**{**vars(obj),"validate_candidate":clone(child,depth+1)})
        if "candidate" in fn.__code__.co_names:
            old=env["candidate"]
            env["candidate"]=NS(**{**vars(old),"retained_evidence":connect_retained(original_candidate,direct_oracle,diagnostic)})
            state["retained_leaf_changes"]+=1
        result=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
        require(result.__code__ is fn.__code__ and result.__defaults__ is fn.__defaults__ and
                result.__closure__ is fn.__closure__,"ALL_FULL_CANDIDATE_CODE_RETAINED")
        state["cloned_functions"].append(fn.__name__)
        return result
    result=clone(function)
    require(state["retained_leaf_changes"]==1,"EXACT_ONE_RETAINED_DIAGNOSTIC_DEPENDENCY")
    return result,state
