"""New actual26 capsule; whole original run002 graph code metadata inverse."""
from types import FunctionType
import successor_runtime_graph_v3 as original
SELF="tools/p09/successor_runtime_graph_v4.py"
CAPSULE={"bytes":14118,"path":"implementation/p09/evidence/p09-361-case160-worker-policy-capsule003.v5.json","sha256":"fdbc31239bf30c972ed1a621a6f685f9d8200a2f4aabe8ec2bf8823163a19e95"}
fn=original.build;code=fn.__code__
if sum(type(x) is int and x==25 for x in code.co_consts)!=1:
    raise ValueError("ONE_ORIGINAL_GRAPH_COUNT_METADATA")
revised=code.replace(co_consts=tuple(26 if type(x) is int and x==25 else x for x in code.co_consts))
if revised.replace(co_consts=code.co_consts)!=code:raise ValueError("WHOLE_ORIGINAL_GRAPH_CODE_INVERSE")
build=FunctionType(revised,dict(fn.__globals__,CAPSULE=CAPSULE),argdefs=fn.__defaults__,closure=fn.__closure__)
build.__kwdefaults__=fn.__kwdefaults__
