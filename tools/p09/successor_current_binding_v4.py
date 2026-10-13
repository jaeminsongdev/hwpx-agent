"""Actual26 full bind: original v3 body with explicit new private dependencies."""
from types import FunctionType
import successor_current_binding_v3 as original
import runtime_successor_manifest_v5 as manifest
import runtime_successor_worker_capsule_v4 as capsule
import successor_runtime_graph_v4 as factory
SELF="tools/p09/successor_current_binding_v4.py"
fn=original.bind;code=fn.__code__
if sum(type(x) is int and x==25 for x in code.co_consts)!=1:
    raise ValueError("ONE_ORIGINAL_BINDING_COUNT_METADATA")
revised=code.replace(co_consts=tuple(26 if type(x) is int and x==25 else x for x in code.co_consts))
if revised.replace(co_consts=code.co_consts)!=code:raise ValueError("WHOLE_ORIGINAL_BINDING_CODE_INVERSE")
bind=FunctionType(revised,dict(fn.__globals__,SELF=SELF,manifest=manifest,capsule=capsule,factory=factory),
    argdefs=fn.__defaults__,closure=fn.__closure__)
bind.__kwdefaults__=fn.__kwdefaults__
