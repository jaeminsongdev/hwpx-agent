"""Run003 whole29 Binding with the original v4 function metadata inverse."""
from types import FunctionType
import successor_current_binding_v4 as original
import runtime_successor_manifest_v6 as manifest
import runtime_successor_worker_capsule_v5 as capsule
import successor_runtime_graph_v5 as factory
SELF="tools/p09/successor_current_binding_v5.py"
fn=original.bind;code=fn.__code__
mapping={26:29,"case160-current-r002-tests":"case160-current-r003-tests"}
if sum(type(x) is int and x==26 for x in code.co_consts)!=1:
    raise ValueError("ONE_ORIGINAL_BINDING_COUNT_METADATA")
revised=code.replace(co_consts=tuple(mapping.get(x,x) if type(x) in (int,str) else x for x in code.co_consts))
inverse={v:k for k,v in mapping.items()}
if revised.replace(co_consts=tuple(inverse.get(x,x) if type(x) in (int,str) else x for x in revised.co_consts))!=code:
    raise ValueError("WHOLE_ORIGINAL_RUN003_BINDING_CODE_INVERSE")
bind=FunctionType(revised,dict(fn.__globals__,SELF=SELF,manifest=manifest,capsule=capsule,factory=factory),
    argdefs=fn.__defaults__,closure=fn.__closure__)
bind.__kwdefaults__=fn.__kwdefaults__
