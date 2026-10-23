"""Explicit candidate-only dependency injection in original private namespaces."""
import sys
from types import FunctionType, SimpleNamespace as NS

SELF='tools/p09/native011_current_epoch_worker_scope.py'
TEST='tools/p09/tests/test_native011_current_epoch_worker_scope.py'


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_WORKER_SCOPE_'+code)


def route(linked,old_pin,new_pin,scope,*,modules=None):
    """Do not replace worker bodies, arguments, defaults, clocks or default modules."""
    worker=linked.original_worker;engine=linked.engine.run_owned
    require(type(worker) is FunctionType and type(engine) is FunctionType
        and linked.engine.worker is worker and linked.state.original is worker,
        'SAME_ORIGINAL_WORKER_AND_ENGINE')
    require(linked.state.attempts==linked.state.calls==0 and not linked.state.completed,
        'BEFORE_ANY_WORKER_ATTEMPT_ONLY')
    scope.pins([old_pin,new_pin]);require(old_pin!=new_pin,'DISTINCT_QUALIFIED_CANDIDATES')
    modules=tuple(sys.modules.values()) if modules is None else tuple(modules)
    environments=[]
    for function in (worker,engine):
        env=function.__globals__
        if not any(env is previous for previous in environments):environments.append(env)
    snapshots=[]
    for env in environments:
        require(not any(getattr(module,'__dict__',None) is env for module in modules),
            'PRIVATE_NAMESPACE_NOT_DEFAULT_MODULE_GLOBALS')
        original=env.get('scope')
        require(original is not None and getattr(original,'EXE_PIN',None)==old_pin,
            'EXACT_PREVIOUS_CANDIDATE_NO_REPEATED_ROUTING')
        snapshots.append((env,dict(env),original))
    args=worker.__globals__.get('arguments')
    require(type(args) is FunctionType,'ORIGINAL_ARGUMENT_FUNCTION')
    before_arguments=tuple(args())
    identities=[(fn,fn.__code__,fn.__defaults__,fn.__kwdefaults__,fn.__closure__) for fn in (worker,engine)]
    for env,_,original in snapshots:env['scope']=NS(**{**vars(original),'EXE_PIN':dict(new_pin)})
    require(tuple(args())==before_arguments,'ORIGINAL_ARGUMENTS_UNCHANGED')
    for env,before,original in snapshots:
        require(set(env)==set(before) and all(env[n] is value for n,value in before.items() if n!='scope'),
            'ONLY_EXPLICIT_SCOPE_DEPENDENCY_REPLACED')
        require(vars(env['scope'])==dict(vars(original),EXE_PIN=dict(new_pin))
            and original.EXE_PIN==old_pin,'ONLY_CANDIDATE_FIELD_NOT_OLD_SCOPE_MUTATION')
    require(all(fn.__code__ is code and fn.__defaults__ is defaults and fn.__kwdefaults__ is kw
        and fn.__closure__ is closure for fn,code,defaults,kw,closure in identities),
        'ORIGINAL_COMPLETE_CODE_DEFAULTS_CLOSURES_RETAINED')
    require(linked.state.attempts==linked.state.calls==0 and not linked.state.completed,'NO_EXECUTION_DURING_ROUTING')
    return dict(original_worker_and_engine_functions_retained=True,original_argument_function_retained=True,
        original_arguments_unchanged=True,private_namespace_count=len(environments),
        old_candidate_preserved=dict(old_pin),new_candidate=dict(new_pin),
        candidate_dependency_only=True,default_modules_mutated=False,worker_executed=False,
        Native_or_metadata_or_readiness_qualified=False)
