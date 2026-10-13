"""Run003 actual29 graph; original full graph code metadata inverse."""
from types import FunctionType
import successor_runtime_graph_v4 as original
SELF="tools/p09/successor_runtime_graph_v5.py"
CAPSULE={"path":"implementation/p09/evidence/p09-361-case160-worker-policy-capsule004.v6.json","bytes":15663,"sha256":"bf2163e976d5c8cf52b83a096984e3343fb73b6bb7ced26ddf5c8dada297b5f6"}
fn=original.build;code=fn.__code__
mapping={26:29,"case160-current-r002-tests":"case160-current-r003-tests"}
if sum(type(x) is int and x==26 for x in code.co_consts)!=1:
    raise ValueError("ONE_ORIGINAL_GRAPH_COUNT_METADATA")
revised=code.replace(co_consts=tuple(mapping.get(x,x) if type(x) in (int,str) else x for x in code.co_consts))
inverse={v:k for k,v in mapping.items()}
if revised.replace(co_consts=tuple(inverse.get(x,x) if type(x) in (int,str) else x for x in revised.co_consts))!=code:
    raise ValueError("WHOLE_ORIGINAL_RUN003_GRAPH_CODE_INVERSE")
build=FunctionType(revised,dict(fn.__globals__,CAPSULE=CAPSULE),argdefs=fn.__defaults__,closure=fn.__closure__)
build.__kwdefaults__=fn.__kwdefaults__
