"""Entire parent32 qualifier body, exact metadata/import projection to34."""
from types import CodeType,FunctionType
import qualify_parent32_binding_r371 as original
SELF="tools/p09/qualify_parent34_binding_r372.py"
OUTPUT="implementation/p09/evidence/p09-361-run004-parent34-binding-code5-r856.v1.json"
MAPPING={
    9:5,
    "test_successor_current_binding_v6":"test_successor_current_binding_v7",
    "test_successor_bounded_graph_bootstrap_v6":"test_successor_bounded_graph_bootstrap_v7",
    "ALL_PARENT32_CODE9":"ALL_PARENT34_CODE5",
    "PASS_RUN004_FULL_PARENT32_BINDING_CODE9_SAME_BOUNDED_GRAPH_NOT_CONTROLLER_OR_GO":
        "PASS_RUN004_FULL_PARENT34_BINDING_CODE5_SAME_BOUNDED_GRAPH_NOT_CONTROLLER_OR_GO"}
def project(code,mapping):
    def value(x):
        if type(x) is CodeType:return project(x,mapping)
        if type(x) is tuple:return tuple(value(v) for v in x)
        return mapping.get(x,x) if type(x) in (int,str) else x
    return code.replace(co_consts=tuple(value(x) for x in code.co_consts))
fn=original.main
changed=project(fn.__code__,MAPPING)
inverse={v:k for k,v in MAPPING.items()}
if project(changed,inverse)!=fn.__code__:raise ValueError("ENTIRE_ORIGINAL_PARENT_QUALIFIER_METADATA_INVERSE")
names=tuple("successor_current_binding_v7" if n=="successor_current_binding_v6" else n for n in changed.co_names)
changed=changed.replace(co_names=names)
if changed.replace(co_names=fn.__code__.co_names)!=project(fn.__code__,MAPPING):
    raise ValueError("ENTIRE_ORIGINAL_PARENT_QUALIFIER_IMPORT_INVERSE")
main=FunctionType(changed,dict(fn.__globals__,SELF=SELF,OUTPUT=OUTPUT),argdefs=fn.__defaults__,closure=fn.__closure__)
main.__kwdefaults__=fn.__kwdefaults__
if __name__=="__main__":raise SystemExit(main())
