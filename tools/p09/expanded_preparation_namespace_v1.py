"""Exact metadata namespace for expanded parent/worker preparation.

Whole code inverse for literal-only receipt suffix projection. No source file,
default module, source scope, guard, budget, Frame or GO predicate is changed.
"""
from types import CodeType,FunctionType,SimpleNamespace as NS

SELF="tools/p09/expanded_preparation_namespace_v1.py"
TEST="tools/p09/tests/test_expanded_preparation_namespace_v1.py"
PROFILE="hwpx-agent.p09-expanded-preparation-namespace/v1"


def require(ok,label):
    if not ok:raise ValueError("EXPANDED_PREPARATION_NAMESPACE_"+label)


def literal_function(fn,mapping):
    require(type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_"),"PRIVATE_FUNCTION_ONLY")
    require(type(mapping) is dict and mapping and len(set(mapping.values()))==len(mapping)
        and all(type(k) is str and type(v) is str and k!=v for k,v in mapping.items()),"CLOSED_LITERAL_MAP")
    counts={key:0 for key in mapping}
    def contains(value,targets):
        if type(value) is CodeType:return any(contains(v,targets) for v in value.co_consts)
        if type(value) in (tuple,frozenset):return any(contains(v,targets) for v in value)
        return type(value) is str and value in targets
    require(not contains(fn.__code__,set(mapping.values())),"NO_PREEXISTING_TARGET_LITERAL")
    def transform(value,pairs,measure=False):
        if type(value) is CodeType:return value.replace(co_consts=tuple(transform(v,pairs,measure) for v in value.co_consts))
        if type(value) is tuple:return tuple(transform(v,pairs,measure) for v in value)
        if type(value) is frozenset:return frozenset(transform(v,pairs,measure) for v in value)
        if type(value) is str and value in pairs:
            if measure:counts[value]+=1
            return pairs[value]
        return value
    code=transform(fn.__code__,mapping,True)
    require(all(v>0 for v in counts.values()),"EVERY_DECLARED_LITERAL_PRESENT")
    require(transform(code,{v:k for k,v in mapping.items()})==fn.__code__,"ENTIRE_RECURSIVE_CODE_INVERSE")
    revised=FunctionType(code,dict(fn.__globals__),argdefs=fn.__defaults__,closure=fn.__closure__)
    revised.__kwdefaults__=fn.__kwdefaults__
    return revised,dict(exact_entire_code_inverse=True,changed_literals=counts,
        original_defaults_closure_and_keywords_retained=True,source_or_default_module_modified=False)


def with_validator(fn,validator):
    result=FunctionType(fn.__code__,dict(fn.__globals__,validate_worker_hint=validator),
        argdefs=fn.__defaults__,closure=fn.__closure__)
    result.__kwdefaults__=fn.__kwdefaults__
    return result


def install(runtime):
    if getattr(runtime,"expanded_preparation_namespace_profile",None)==PROFILE:return
    validate=runtime.validate_worker_hint
    originals=None
    if ".compact.v4.json" not in validate.__code__.co_consts:
        for fn in (runtime.worker_hint,runtime.reconstruct_worker_graph):
            for cell in fn.__closure__ or ():
                value=cell.cell_contents
                if type(value) is NS and set(vars(value))=={"worker_hint","validate_worker_hint","reconstruct_worker_graph","current_input_scope"}:
                    require(originals is None or originals is value,"ONE_ORIGINAL_SNAPSHOT")
                    originals=value
        require(originals is not None,"ORIGINAL_VALIDATOR_DEPENDENCY_REQUIRED")
        validate=originals.validate_worker_hint
    revised,proof=literal_function(validate,{".compact.v4.json":".compact.v9.json"})
    if originals is None:
        runtime.validate_worker_hint=revised
        validate.__globals__["validate_worker_hint"]=revised
    else:
        originals.validate_worker_hint=revised
        originals.worker_hint=with_validator(originals.worker_hint,revised)
        originals.reconstruct_worker_graph=with_validator(originals.reconstruct_worker_graph,revised)
    for name in ("owned_worker_entry","qualify_factory"):
        fn=getattr(runtime,name)
        changed,proof=literal_function(fn,{".v4.json":".v9.json"})
        fn.__globals__[name]=changed;setattr(runtime,name,changed)
    runtime.expanded_preparation_namespace_profile=PROFILE


def retarget_worker(runtime,path):
    require(type(path) is str and path.startswith("tools/p09/") and path.endswith(".py"),"EXPLICIT_WORKER_ENTRY")
    for fn in vars(runtime).values():
        if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_current_queue_successor_runtime"):
            fn.__globals__["SELF"]=path
    runtime.SELF=path
