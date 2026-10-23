"""One measured inventory identity across actual engine and full checker.

Only the explicit inventory data and its existing dependency slots change.
Original budget/cost/evidence/projector bodies, actual observations, final
sample, decoder, product window, readiness, resource and600 guards remain.
"""
import sys
from types import FunctionType, SimpleNamespace as NS

SELF='tools/p09/native011_current_epoch_runtime_cost.py'
TEST='tools/p09/tests/test_native011_current_epoch_runtime_cost.py'
ORACLE='tools/p09/held_native_view_oracle_v1.py'
PARENT_ORACLE='tools/p09/native011_parent_oracle.py'


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_RUNTIME_COST_'+code)


def clone(original,env,code=None):
    result=FunctionType(original.__code__ if code is None else code,env,
        argdefs=original.__defaults__,closure=original.__closure__)
    result.__kwdefaults__=original.__kwdefaults__
    return result


def bind_family(direct,actual_requests,binder):
    budget,proof=binder(direct.runtime_budget,actual_requests)
    result=dict(vars(direct));result.update(runtime_budget=budget,INVENTORY_REQUESTS=actual_requests)
    for name in ('cost','retained_evidence','project_checker'):
        original=getattr(direct,name)
        require(type(original) is FunctionType and original.__name__==name
            and original.__code__.co_filename.replace('\\','/').endswith(ORACLE),
            'EXACT_ORIGINAL_COST_EVIDENCE_PROJECTOR_FAMILY')
        require(original.__globals__.get('INVENTORY_REQUESTS')==167,'ORIGINAL167_FAMILY_NOT_ALREADY_BOUND')
        if name=='project_checker':
            changes=dict(cost=result['cost'],mechanics_projection=direct.mechanics_projection)
        else:changes=dict(runtime_budget=budget,INVENTORY_REQUESTS=actual_requests)
        result[name]=clone(original,dict(original.__globals__,**changes))
    current=NS(**result)
    require(current.cost.__globals__['runtime_budget'] is budget
        and current.retained_evidence.__globals__['runtime_budget'] is budget
        and current.project_checker.__globals__['cost'] is current.cost,
        'ONE_SAME_BUDGET_DEPENDENCY_ALL_FOUR_PATHS')
    return current,dict(proof,full_cost_evidence_projector_code_retained=True,
        current_existing_mechanics_projection_retained=True,original_direct_namespace_mutated=False)


def connect_engine(engine,direct,actual_requests,binder,*,modules=None):
    function=engine.run_owned
    require(type(function) is FunctionType and function.__globals__.get('runtime_budget') is direct.runtime_budget,
        'ACTUAL_ENGINE_USES_SAME_PREVIOUS_DIRECT_BUDGET')
    modules=tuple(sys.modules.values()) if modules is None else tuple(modules)
    env=function.__globals__
    require(not any(getattr(module,'__dict__',None) is env for module in modules),'PRIVATE_ENGINE_NOT_DEFAULT_MODULE')
    current,proof=bind_family(direct,actual_requests,binder)
    before=dict(env);env['runtime_budget']=current.runtime_budget
    require(set(env)==set(before) and all(env[name] is value for name,value in before.items() if name!='runtime_budget')
        and engine.run_owned is function,'ONLY_ENGINE_BUDGET_DEPENDENCY_NOT_BODY_OR_OBSERVATIONS')
    return current,dict(proof,actual_engine_function_identity_retained=True,
        actual_engine_budget_dependency_connected=True,engine_body_executed=False)


def oracle_connection(oracle,actual_requests):
    require(type(actual_requests) is int and 1<=actual_requests<=8192,'MEASURED_BOUNDED_COUNT')
    original=oracle.complete_cost
    require(type(original) is FunctionType and original.__name__=='complete_cost'
        and original.__code__.co_filename.replace('\\','/').endswith(PARENT_ORACLE),
        'EXACT_ORIGINAL_COMPLETE_COST_FUNCTION')
    constants=list(original.__code__.co_consts)
    slots=[i for i,value in enumerate(constants) if type(value) is int and value==167]
    require(len(slots)==1,'ONE_ORIGINAL167_INVENTORY_DATA_SLOT')
    index=slots[0];constants[index]=actual_requests
    code=original.__code__.replace(co_consts=tuple(constants));undo=list(code.co_consts);undo[index]=167
    require(code.replace(co_consts=tuple(undo))==original.__code__,'COMPLETE_COST_CODE_FULL_INVERSE')
    cost=clone(original,original.__globals__,code)
    connected=clone(oracle.connect,dict(oracle.connect.__globals__,complete_cost=cost))
    return NS(**{**vars(oracle),'complete_cost':cost,'connect':connected}),dict(
        original_inventory_requests=167,actual_inventory_requests=actual_requests,
        entire_original_complete_cost_code_inverse=True,entire_original_checker_connect_code_retained=True,
        original600_margin60_shared5_readiness15_product10_changed=False,
        original_default_oracle_namespace_mutated=False,actual_runtime_qualified=False)


def connect_checker(checker,actual_requests,binder):
    env=checker.environment
    require(not checker.projectors and env['base'].CONFIG.index==165,'ACTUAL_CURRENT165_CHECKER_UNEXECUTED')
    original=env['prior'];direct,proof=bind_family(original.DIRECT,actual_requests,binder)
    before=dict(env);env['prior']=NS(**{**vars(original),'DIRECT':direct})
    require(all(env[name] is value for name,value in before.items() if name!='prior')
        and set(env)==set(before),'ONLY_DECLARED_CHECKER_PRIOR_BUDGET_DEPENDENCY')
    return direct,dict(proof,entire_original_validator_and_checker_environment_retained=True,
        independent_checker_body_executed=False,observed_candidate_or_original_records_mutated=False)
